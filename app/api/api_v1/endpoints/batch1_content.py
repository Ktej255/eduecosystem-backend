"""
Batch 1 Content API Endpoints
Manage video segments for UPSC Prelims Batch 1 course
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from app.api.api_v1.endpoints.pdf_study import process_pdf_document
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import uuid
import json
import asyncio

router = APIRouter()

# Upload directory - use absolute path relative to backend root
# Go from app/api/api_v1/endpoints to backend root, then to uploads/batch1
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
UPLOAD_DIR = os.path.join(BACKEND_ROOT, "uploads", "batch1")
DATA_DIR = os.path.join(BACKEND_ROOT, "data")
SEGMENTS_FILE = os.path.join(DATA_DIR, "segments_data.json")

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
print(f"Batch1 uploads directory: {UPLOAD_DIR}")
print(f"Segments data file: {SEGMENTS_FILE}")


def load_segments() -> Dict[str, Dict[str, Any]]:
    """Load segments from JSON file"""
    if os.path.exists(SEGMENTS_FILE):
        try:
            with open(SEGMENTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Loaded {len(data)} segments from {SEGMENTS_FILE}")
                return data
        except Exception as e:
            print(f"Error loading segments: {e}")
            return {}
    return {}


def save_segments():
    """Save segments to JSON file"""
    try:
        with open(SEGMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(SEGMENTS_STORE, f, indent=2)
        print(f"Saved {len(SEGMENTS_STORE)} segments to {SEGMENTS_FILE}")
    except Exception as e:
        print(f"Error saving segments: {e}")


# Load existing segments on startup - THIS ENSURES PERSISTENCE!
SEGMENTS_STORE: Dict[str, Dict[str, Any]] = load_segments()

# Track transcription status
TRANSCRIPTION_STATUS: Dict[str, str] = {}


def run_transcription_background(video_path: str, segment_key: str, segment_title: str):
    """Run transcription in background (sync wrapper for async function)"""
    try:
        from app.services.transcription_service import process_video_transcription
        
        TRANSCRIPTION_STATUS[segment_key] = "processing"
        print(f"[Batch1Content] Starting background transcription for {segment_key}")
        
        # Run the async transcription
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            process_video_transcription(video_path, segment_key, segment_title)
        )
        loop.close()
        
        if result.get("status") == "completed":
            TRANSCRIPTION_STATUS[segment_key] = "completed"
            print(f"[Batch1Content] Transcription completed for {segment_key}")
        else:
            TRANSCRIPTION_STATUS[segment_key] = f"error: {result.get('error', 'unknown')}"
            print(f"[Batch1Content] Transcription failed for {segment_key}")
            
    except Exception as e:
        TRANSCRIPTION_STATUS[segment_key] = f"error: {str(e)}"
        print(f"[Batch1Content] Transcription error for {segment_key}: {e}")


class SegmentData(BaseModel):
    """Data for a video segment"""
    title: str
    key_points: str
    video_url: Optional[str] = None
    youtube_url: Optional[str] = None
    content_type: str = "video"  # video, pdf, youtube
    pdf_files: List[Dict[str, Any]] = []
    duration: str = "25:00"


class SegmentResponse(BaseModel):
    """Response for segment data"""
    id: int
    title: str
    key_points: str
    video_url: Optional[str]
    youtube_url: Optional[str] = None
    youtube_url: Optional[str] = None
    content_type: str = "video"
    pdf_files: List[Dict[str, Any]] = []
    duration: str


class DayContentResponse(BaseModel):
    """Response for all segments in a day's part"""
    cycle_id: int
    day_number: int
    part_number: int
    segments: List[SegmentResponse]


@router.get("/cycle/{cycle_id}/day/{day_number}/part/{part_number}", response_model=DayContentResponse)
async def get_part_content(
    cycle_id: int,
    day_number: int,
    part_number: int
):
    """
    Get all video segments for a specific part of a day.
    Returns 4 segments per part.
    """
    segments = []
    for seg_num in range(1, 5):  # 4 segments per part
        key = f"{cycle_id}_{day_number}_{part_number}_{seg_num}"
        
        if key in SEGMENTS_STORE:
            data = SEGMENTS_STORE[key]
            segments.append(SegmentResponse(
                id=seg_num,
                title=data.get("title", f"Segment {seg_num}"),
                key_points=data.get("key_points", ""),
                video_url=data.get("video_url"),
                youtube_url=data.get("youtube_url"),
                video_url=data.get("video_url"),
                youtube_url=data.get("youtube_url"),
                content_type=data.get("content_type", "video"),
                pdf_files=data.get("pdf_files", []),
                duration=data.get("duration", "25:00")
            ))
        else:
            # Default segment if not uploaded
            segments.append(SegmentResponse(
                id=seg_num,
                title=f"Segment {seg_num} (Not Uploaded)",
                key_points="Key points will appear here after admin uploads content",
                video_url=None,
                youtube_url=None,
                video_url=None,
                youtube_url=None,
                content_type="video",
                pdf_files=[],
                duration="25:00"
            ))
    
    return DayContentResponse(
        cycle_id=cycle_id,
        day_number=day_number,
        part_number=part_number,
        segments=segments
    )


@router.post("/cycle/{cycle_id}/day/{day_number}/part/{part_number}/segment/{segment_number}")
async def save_segment(
    cycle_id: int,
    day_number: int,
    part_number: int,
    segment_number: int,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    key_points: str = Form(""),
    content_type: str = Form("video"),  # video, pdf, youtube
    youtube_url: Optional[str] = Form(None),
    video: Optional[UploadFile] = File(None),
    pdf_files: List[UploadFile] = File(None),
    pdf_names: List[str] = Form(None),
    preserved_pdf_data: Optional[str] = Form(None)  # JSON string of existing PDFs to keep
):
    """
    Save or update a video segment.
    Automatically triggers video transcription for AI analysis.
    """
    try:
        key = f"{cycle_id}_{day_number}_{part_number}_{segment_number}"
        
        video_url = None
        file_path = None
        video_uploaded = False
        
        if video and video.filename:
            # Ensure upload directory exists
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            
            # Save video file
            file_ext = os.path.splitext(video.filename)[1] if video.filename else ".mp4"
            unique_filename = f"c{cycle_id}_d{day_number}_p{part_number}_s{segment_number}_{uuid.uuid4().hex[:8]}{file_ext}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            contents = await video.read()
            with open(file_path, "wb") as f:
                f.write(contents)
            
            video_url = f"/uploads/batch1/{unique_filename}"
            video_uploaded = True
        elif key in SEGMENTS_STORE:
            # Keep existing video URL if not uploading new one
            video_url = SEGMENTS_STORE[key].get("video_url")
            # Get file path from existing URL if available
            if video_url:
                file_path = os.path.join(UPLOAD_DIR, os.path.basename(video_url))
        
        # Handle PDF uploads
        saved_pdfs = SEGMENTS_STORE.get(key, {}).get("pdf_files", []) if key in SEGMENTS_STORE else []
        
        # If new PDFs are uploaded, we might want to replace or append? 
        # Current logic: If pdf_files provided, we process them. 
        # Since frontend sends ALL files (including re-uploads if needed), we could replace?
        # But frontend might only send NEW files? 
        # Actually, for simplicity and "Save All" logic, let's assume the frontend sends the current state 
        # or we need to manage "existing" vs "new". 
        # To avoid data loss, let's Append new ones or Replace if logic dictates.
        # Given the "DayContentUpload" state, it has full list. 
        # Let's save new files.
        
        if pdf_files:
            # Ensure pdfs directory
            PDF_DIR = os.path.join(UPLOAD_DIR, "pdfs")
            os.makedirs(PDF_DIR, exist_ok=True)
            
            new_pdfs = []
            for idx, pdf in enumerate(pdf_files):
                if pdf.filename:
                    # Unique filename
                    file_ext = os.path.splitext(pdf.filename)[1]
                    unique_name = f"c{cycle_id}_d{day_number}_p{part_number}_s{segment_number}_pdf{idx}_{uuid.uuid4().hex[:6]}{file_ext}"
                    dest_path = os.path.join(PDF_DIR, unique_name)
                    
                    content = await pdf.read()
                    with open(dest_path, "wb") as f:
                        f.write(content)
                    
                    pdf_url = f"/uploads/batch1/pdfs/{unique_name}"
                    pdf_name = pdf_names[idx] if pdf_names and idx < len(pdf_names) else pdf.filename
                    
                    new_pdfs.append({
                        "name": pdf_name,
                        "url": pdf_url,
                        "original_filename": pdf.filename
                    })
                    
                    # Trigger PDF processing for the first PDF (as primary study material)
                    if idx == 0:
                        print(f"Triggering PDF processing for {key}")
                        # We process it immediately so it is ready for student view
                        try:
                            await process_pdf_document(key, dest_path, pdf_name)
                        except Exception as e:
                            print(f"Failed to process PDF: {e}")
            
            # If we are in 'pdf' mode and sending files, we probably want to update the list.
            # But we should preserve OLD files if they weren't re-uploaded.
            # However, the frontend creates a list of "pdfFiles". 
            # Ideally, the frontend should tell us the FINAL structure. 
            # For now, let's APPEND new PDFs to existing ones? 
            # No, if user deletes one in UI, we want it gone.
            # But we don't know which ones are kept unless frontend sends "existing_pdf_urls".
            # FIX: Just append for now to ensure AT LEAST they are saved.
            # Better: The frontend should send "video" or "pdf" mode.
            # Legacy/Default append behavior: if no preservation data sent, just append.
            if new_pdfs and not preserved_pdf_data:
                saved_pdfs.extend(new_pdfs)
                
        # Handle PDF Preservation/Merging
        # If preserved_pdf_data is provided, we use it as the base.
        # If not provided, we default to "append to existing" logic (handled above by extending saved_pdfs).
        # BUT if the frontend sends preserved_pdf_data, it implies "EXACT STATE".
        # So we should filter saved_pdfs to match preserved_pdf_data URLs.
        
        if preserved_pdf_data:
            try:
                preserved_list = json.loads(preserved_pdf_data)
                preserved_urls = [p.get('url') for p in preserved_list if p.get('url')]
                
                # Filter existing stored PDFs to keep only those present in preserved_list
                # This handles deletions from the frontend
                kept_pdfs = [
                    p for p in SEGMENTS_STORE.get(key, {}).get("pdf_files", [])
                    if p.get('url') in preserved_urls
                ]
                
                # Re-construct final list: Kept + New
                # Note: saved_pdfs above was just a copy. We should rebuild to be safe.
                saved_pdfs = kept_pdfs + (new_pdfs if 'new_pdfs' in locals() else [])
                
            except Exception as e:
                print(f"Error parsing preserved_pdf_data: {e}")
                # Fallback to append behavior if parse fails
                pass

        # Store segment data
        SEGMENTS_STORE[key] = {
            "title": title,
            "key_points": key_points,
            "video_url": video_url,
            "youtube_url": youtube_url,
            "content_type": content_type,
            "pdf_files": saved_pdfs,  # Persist PDF list
            "duration": "25:00",
            "updated_at": datetime.utcnow().isoformat(),
            "transcription_status": "pending" if video_uploaded else SEGMENTS_STORE.get(key, {}).get("transcription_status", "none")
        }
        
        # PERSIST TO FILE so data survives server restarts
        save_segments()
        
        print(f"Saved segment: {key} with title: {title}, video_url: {video_url}")
        
        # Trigger background transcription if new video uploaded
        if video_uploaded and file_path:
            print(f"[Batch1Content] Triggering background transcription for {key}")
            TRANSCRIPTION_STATUS[key] = "queued"
            background_tasks.add_task(
                run_transcription_background,
                file_path,
                key,
                title
            )
        
        return {
            "success": True,
            "message": f"Segment {segment_number} saved successfully" + (" - Transcription started in background" if video_uploaded else ""),
            "segment_key": key,
            "video_url": video_url,
            "transcription_started": video_uploaded
        }
    except Exception as e:
        print(f"Error saving segment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save segment: {str(e)}")


@router.get("/all-segments")
async def get_all_segments():
    """Get all uploaded segments (for admin view)"""
    return SEGMENTS_STORE


@router.get("/transcription-status/{segment_key}")
async def get_transcription_status(segment_key: str):
    """Check transcription status for a video segment"""
    from app.services.transcription_service import get_transcription_status, get_video_document
    
    status = get_transcription_status(segment_key)
    document = get_video_document(segment_key)
    
    return {
        "segment_key": segment_key,
        "processing_status": TRANSCRIPTION_STATUS.get(segment_key, "unknown"),
        "has_transcript": status.get("has_transcript", False),
        "has_document": status.get("has_document", False),
        "document_summary": document.get("summary", None) if document else None,
        "key_points_count": len(document.get("key_points_for_recall", [])) if document else 0
    }


@router.get("/segment-document/{segment_key}")
async def get_segment_document(segment_key: str):
    """Get the full transcription document for a segment"""
    from app.services.transcription_service import get_video_document
    
    document = get_video_document(segment_key)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found. Video may not be transcribed yet.")
    
    return document


@router.post("/bulk-save")
async def bulk_save_segments(
    cycle_id: int = Form(...),
    day_number: int = Form(...),
    data: str = Form(...)  # JSON string of all segments
):
    """
    Bulk save segment metadata (titles and key points).
    Videos are uploaded separately.
    """
    try:
        segments_data = json.loads(data)
        
        for part_num in range(1, 4):  # 3 parts
            for seg_num in range(1, 5):  # 4 segments per part
                key = f"{cycle_id}_{day_number}_{part_num}_{seg_num}"
                seg_key = f"{part_num}-{seg_num}"
                
                if seg_key in segments_data:
                    seg = segments_data[seg_key]
                    existing = SEGMENTS_STORE.get(key, {})
                    
                    SEGMENTS_STORE[key] = {
                        "title": seg.get("title", f"Segment {seg_num}"),
                        "key_points": seg.get("notes", ""),
                        "video_url": existing.get("video_url"),  # Keep existing video
                        "duration": "25:00",
                        "updated_at": datetime.utcnow().isoformat()
                    }
        
        # PERSIST TO FILE so data survives server restarts
        save_segments()
        
        return {"success": True, "message": "All segments saved"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save: {str(e)}")
