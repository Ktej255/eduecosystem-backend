"""
PDF Study API Endpoints

Handles PDF upload, page extraction, and recall evaluation for Batch 1 self-study.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import os
import json
import base64

router = APIRouter()

# Storage paths
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
UPLOAD_DIR = os.path.join(BACKEND_ROOT, "uploads", "pdfs")
DATA_DIR = os.path.join(BACKEND_ROOT, "data")
PDF_DATA_FILE = os.path.join(DATA_DIR, "pdf_study_data.json")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# In-memory store (persisted to JSON)
PDF_STORE = {}

def load_pdf_data():
    global PDF_STORE
    if os.path.exists(PDF_DATA_FILE):
        try:
            with open(PDF_DATA_FILE, 'r') as f:
                PDF_STORE = json.load(f)
        except:
            PDF_STORE = {}
    return PDF_STORE

def save_pdf_data():
    with open(PDF_DATA_FILE, 'w') as f:
        json.dump(PDF_STORE, f, indent=2)

# Load on startup
load_pdf_data()


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
    
    segment_key = f"{cycle_id}_{day_number}_{segment_number}"
    
    # Save PDF file
    file_path = os.path.join(UPLOAD_DIR, f"{segment_key}.pdf")
    content = await pdf_file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Extract pages
    
    # Process the PDF using the shared function
    success = await process_pdf_document(segment_key, file_path, pdf_file.filename)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process PDF")
    
    # Return success based on updated store
    page_count = PDF_STORE.get(segment_key, {}).get("page_count", 0)
    
    return {
        "success": True,
        "segment_key": segment_key,
        "page_count": page_count,
        "message": f"PDF uploaded with {page_count} pages"
    }

async def process_pdf_document(segment_key: str, file_path: str, title: str = "PDF Document"):
    """
    Process a PDF file: extract text and images for each page.
    Updates PDF_STORE with the processed data.
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
        
        # Store metadata
        PDF_STORE[segment_key] = {
            "pdf_path": file_path,
            "page_count": len(pages_data),
            "pages": pages_data,
            "uploaded_at": datetime.utcnow().isoformat(),
            "title": title
        }
        save_pdf_data()
        print(f"Successfully processed PDF for {segment_key} with {len(pages_data)} pages")
        return True
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return False


@router.get("/segment/{segment_key}")
async def get_pdf_segment(segment_key: str):
    """Get PDF metadata for a segment (without full page data)."""
    if segment_key not in PDF_STORE:
        raise HTTPException(status_code=404, detail="PDF not found for this segment")
    
    data = PDF_STORE[segment_key]
    return {
        "segment_key": segment_key,
        "page_count": data["page_count"],
        "title": data.get("title"),
        "uploaded_at": data.get("uploaded_at")
    }


@router.get("/check/{segment_key}")
async def check_pdf_availability(segment_key: str):
    """Check if a PDF is available for a given segment. Used by frontend to show Video/PDF options."""
    load_pdf_data()  # Reload to get latest data
    available = segment_key in PDF_STORE
    return {
        "segment_key": segment_key,
        "available": available,
        "page_count": PDF_STORE.get(segment_key, {}).get("page_count", 0) if available else 0
    }



@router.get("/page/{segment_key}/{page_number}")
async def get_pdf_page(segment_key: str, page_number: int):
    """Get a single page content (text + image) for student study."""
    if segment_key not in PDF_STORE:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    data = PDF_STORE[segment_key]
    if page_number < 1 or page_number > data["page_count"]:
        raise HTTPException(status_code=404, detail="Page not found")
    
    page = data["pages"][page_number - 1]
    return {
        "segment_key": segment_key,
        "page_number": page_number,
        "total_pages": data["page_count"],
        "text": page["text"],
        "image_base64": page["image_base64"]
    }


@router.post("/evaluate-recall", response_model=RecallEvaluationResponse)
async def evaluate_recall(request: RecallEvaluationRequest):
    """
    Evaluate student's audio recall against the PDF page content.
    Uses Gemini to transcribe audio and compare with page text.
    """
    if request.segment_key not in PDF_STORE:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    data = PDF_STORE[request.segment_key]
    if request.page_number < 1 or request.page_number > data["page_count"]:
        raise HTTPException(status_code=404, detail="Page not found")
    
    page = data["pages"][request.page_number - 1]
    page_text = page["text"]
    
    # Use Gemini for audio transcription and evaluation
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
