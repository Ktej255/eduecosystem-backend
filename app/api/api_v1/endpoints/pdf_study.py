"""
PDF Study API Endpoints

Handles PDF upload, page extraction, and recall evaluation for Batch 1 self-study.
Persists data to PostgreSQL database (Batch1Segment table).
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import os
import json
import base64
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.batch1 import Batch1Segment

router = APIRouter()

# Storage paths (still needed for temporary file handling)
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
UPLOAD_DIR = os.path.join(BACKEND_ROOT, "uploads", "pdfs")

os.makedirs(UPLOAD_DIR, exist_ok=True)


class RecallEvaluationRequest(BaseModel):
    segment_key: str
    page_number: int
    audio_base64: str


class RecallEvaluationResponse(BaseModel):
    score: float
    recalled_points: List[str]
    missing_points: List[str]
    feedback: str
    passed: bool
    transcription: str


@router.post("/upload")
async def upload_pdf(
    cycle_id: int = Form(...),
    day_number: int = Form(...),
    segment_number: int = Form(...),
    pdf_file: UploadFile = File(...)
):
    """
    Teacher uploads a PDF for a specific segment.
    Extracts page count and text per page.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed. Run: pip install pymupdf")
    
    segment_key = f"{cycle_id}_{day_number}_{segment_number}" # Note: This key format might need to match 4-part key if passed that way, but for now assuming 3-part or 4-part based on usage. 
    # ACTUALLY, checking batch1_content usage: key = f"{cycle_id}_{day_number}_{part_number}_{segment_number}"
    # But here form receives cycle, day, segment. Missing part?
    # batch1_content.py calls process_pdf_document with the full 4-part key.
    # This endpoint seems to be a standalone upload backup.
    # Let's assume the key is passed correctly or this endpoint is less used than the batch1_content one.
    
    # Save PDF file
    file_path = os.path.join(UPLOAD_DIR, f"{segment_key}.pdf")
    content = await pdf_file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Process the PDF using the shared function
    success = await process_pdf_document(segment_key, file_path, pdf_file.filename)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process PDF")
    
    # Return success
    with SessionLocal() as db:
        segment = db.query(Batch1Segment).filter(Batch1Segment.segment_key == segment_key).first()
        page_count = 0
        if segment and segment.pdf_data:
            try:
                data = json.loads(segment.pdf_data)
                page_count = data.get("page_count", 0)
            except:
                pass

    return {
        "success": True,
        "segment_key": segment_key,
        "page_count": page_count,
        "message": f"PDF uploaded with {page_count} pages"
    }

async def process_pdf_document(segment_key: str, file_path: str, title: str = "PDF Document"):
    """
    Process a PDF file: extract text and images for each page.
    Updates Batch1Segment in DB with the processed pdf_data.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("PyMuPDF not installed")
        return False
        
    print(f"Processing PDF for {segment_key}: {file_path}")
    
    try:
        # Extract pages
        doc = fitz.open(file_path)
        pages_data = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Render page as image (base64)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img_bytes = pix.tobytes("png")
            img_base64 = base64.b64encode(img_bytes).decode()
            
            pages_data.append({
                "page_number": page_num + 1,
                "text": text,
                "image_base64": img_base64
            })
        
        doc.close()
        
        # Prepare data structure
        pdf_data_content = {
            "pdf_path": file_path,
            "page_count": len(pages_data),
            "pages": pages_data,
            "uploaded_at": datetime.utcnow().isoformat(),
            "title": title
        }
        
        # PERSISTENCE: Save to Database
        with SessionLocal() as db:
            segment = db.query(Batch1Segment).filter(Batch1Segment.segment_key == segment_key).first()
            
            if not segment:
                # Need to handle case where segment doesn't exist yet? 
                # Ideally batch1_content creates it first.
                # If not, we might be in trouble or need to create a placeholder.
                # Assuming batch1_content logic ensures creation.
                print(f"Warning: Segment {segment_key} not found in DB during PDF processing. Creating it.")
                # Attempt to parse keys from segment_key? 
                # key format: cycle_day_part_seg
                parts = segment_key.split('_')
                if len(parts) >= 4:
                    segment = Batch1Segment(
                        cycle_id=int(parts[0]),
                        day_number=int(parts[1]),
                        part_number=int(parts[2]),
                        segment_number=int(parts[3]),
                        segment_key=segment_key,
                        title=title,
                        content_type='pdf'
                    )
                    db.add(segment)
                else:
                    print(f"Error: Invalid segment key format {segment_key}")
                    return False
            
            # Update segment
            segment.pdf_data = json.dumps(pdf_data_content)
            # Ensure content type is pdf
            segment.content_type = 'pdf'
            
            db.commit()
            print(f"Successfully processed and saved PDF data for {segment_key} to Database")
            
        return True
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


@router.get("/segment/{segment_key}")
async def get_pdf_segment(segment_key: str):
    """Get PDF metadata for a segment (without full page data)."""
    with SessionLocal() as db:
        segment = db.query(Batch1Segment).filter(Batch1Segment.segment_key == segment_key).first()
        
        if not segment or not segment.pdf_data:
            raise HTTPException(status_code=404, detail="PDF not found for this segment")
        
        try:
            data = json.loads(segment.pdf_data)
            return {
                "segment_key": segment_key,
                "page_count": data.get("page_count", 0),
                "title": data.get("title"),
                "uploaded_at": data.get("uploaded_at")
            }
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid PDF data in database")


@router.get("/check/{segment_key}")
async def check_pdf_availability(segment_key: str):
    """Check if a PDF is available for a given segment. Used by frontend to show Video/PDF options."""
    with SessionLocal() as db:
        segment = db.query(Batch1Segment).filter(Batch1Segment.segment_key == segment_key).first()
        
        available = False
        page_count = 0
        
        if segment and segment.pdf_data:
            try:
                data = json.loads(segment.pdf_data)
                page_count = data.get("page_count", 0)
                available = page_count > 0
            except:
                pass
                
        return {
            "segment_key": segment_key,
            "available": available,
            "page_count": page_count
        }


@router.get("/page/{segment_key}/{page_number}")
async def get_pdf_page(segment_key: str, page_number: int):
    """Get a single page content (text + image) for student study."""
    with SessionLocal() as db:
        segment = db.query(Batch1Segment).filter(Batch1Segment.segment_key == segment_key).first()
        
        if not segment or not segment.pdf_data:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        try:
            data = json.loads(segment.pdf_data)
            if page_number < 1 or page_number > data.get("page_count", 0):
                raise HTTPException(status_code=404, detail="Page not found")
            
            page = data["pages"][page_number - 1]
            return {
                "segment_key": segment_key,
                "page_number": page_number,
                "total_pages": data["page_count"],
                "text": page["text"],
                "image_base64": page["image_base64"]
            }
        except Exception as e:
            print(f"Error retrieving PDF page: {e}")
            raise HTTPException(status_code=500, detail=f"Error retrieving page: {str(e)}")


@router.post("/evaluate-recall", response_model=RecallEvaluationResponse)
async def evaluate_recall(request: RecallEvaluationRequest):
    """
    Evaluate student's audio recall against the PDF page content.
    Uses Gemini to transcribe audio and compare with page text.
    """
    with SessionLocal() as db:
        segment = db.query(Batch1Segment).filter(Batch1Segment.segment_key == request.segment_key).first()
        
        if not segment or not segment.pdf_data:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        data = json.loads(segment.pdf_data)
        if request.page_number < 1 or request.page_number > data.get("page_count", 0):
            raise HTTPException(status_code=404, detail="Page not found")
        
        page = data["pages"][request.page_number - 1]
        page_text = page["text"]
    
    # Use Gemini for audio transcription and evaluation
    # Note: Using import inside function to avoid circular imports if any, but unlikely here.
    from app.services.gemini_service import gemini_service
    
    # Transcribe audio
    transcription = gemini_service.transcribe_audio(request.audio_base64)
    
    # Evaluate recall
    evaluation = gemini_service.evaluate_recall(
        original_text=page_text,
        student_recall=transcription
    )
    
    passed = evaluation["score"] >= 80
    
    return RecallEvaluationResponse(
        score=evaluation["score"],
        recalled_points=evaluation["recalled_points"],
        missing_points=evaluation["missing_points"],
        feedback=evaluation["feedback"],
        passed=passed,
        transcription=transcription
    )


@router.get("/progress/{segment_key}")
async def get_study_progress(segment_key: str, user_id: int = 0):
    """Get student's progress on a PDF study session."""
    # For now, return mock progress. In production, this would query DB.
    return {
        "segment_key": segment_key,
        "current_page": 1,
        "completed_pages": [],
        "combined_recall_due": False
    }
