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
import tempfile
import urllib.request

# Database imports for persistence
from app.db.session import SessionLocal
from app.models.batch1 import Batch1Segment
from app.core.config import settings

# Optional S3 import
try:
    import boto3
except ImportError:
    boto3 = None

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
    video_url: Optional[str] = None
    youtube_url: Optional[str] = None
    content_type: str = "video"
    pdf_files: List[Dict[str, Any]] = []
    duration: str = "25:00"
    
    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


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
    # --- PERSISTENCE FIX: Read from DB ---
    from app.db.session import SessionLocal
    from app.models.batch1 import Batch1Segment
    
    with SessionLocal() as db:
        segments = []
        for seg_num in range(1, 5):  # 4 segments per part
            key = f"{cycle_id}_{day_number}_{part_number}_{seg_num}"
            
            # Query DB
            segment_data = db.query(Batch1Segment).filter(Batch1Segment.segment_key == key).first()
            
            if segment_data:
                # Parse PDF list
                pdf_list = []
                if segment_data.pdf_files:
                    try:
                        pdf_list = json.loads(segment_data.pdf_files)
                        # CRITICAL FIX: Prepend base URL for locally stored files
                        for pdf in pdf_list:
                            if pdf.get("url", "").startswith("/uploads"):
                                pdf["url"] = f"{settings.BASE_URL}{pdf['url']}"
                    except:
                        pass
                
                # Also fix video_url if local
                video_url = segment_data.video_url
                if video_url and video_url.startswith("/uploads"):
                    video_url = f"{settings.BASE_URL}{video_url}"
                
                segments.append(SegmentResponse(
                    id=seg_num,
                    title=segment_data.title,
                    key_points=segment_data.key_points or "",
                    video_url=video_url,
                    youtube_url=segment_data.youtube_url,
                    content_type=segment_data.content_type or "video",
                    pdf_files=pdf_list,
                    duration=segment_data.duration or "25:00"
                ))
            else:
                # Default segment if not uploaded
                segments.append(SegmentResponse(
                    id=seg_num,
                    title=f"Segment {seg_num} (Not Uploaded)",
                    key_points="Key points will appear here after admin uploads content",
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
        # --- PERSISTENCE: Database & S3 ---
        key = f"{cycle_id}_{day_number}_{part_number}_{segment_number}"
        
        pending_pdf_task = None
        pending_cleanup_file = None
        
        # Create database session
        with SessionLocal() as db:
            # Check if segment exists
            segment = db.query(Batch1Segment).filter(Batch1Segment.segment_key == key).first()
            if not segment:
                segment = Batch1Segment(
                    cycle_id=cycle_id,
                    day_number=day_number,
                    part_number=part_number,
                    segment_number=segment_number,
                    segment_key=key,
                    title=title or f"Segment {segment_number}"
                )
                db.add(segment)
            
            # Update common fields
            segment.title = title
            segment.key_points = key_points
            segment.duration = "25:00"
            
            # Update content_type if provided
            if content_type:
                segment.content_type = content_type

            video_uploaded = False
            file_path_for_transcription = None  # Local path for transcription service

            # 1. Video Upload
            if video and video.filename:
                file_ext = os.path.splitext(video.filename)[1]
                file_name = f"c{cycle_id}_d{day_number}_p{part_number}_s{segment_number}_{uuid.uuid4().hex[:8]}{file_ext}"
                
                # Check if S3 is configured and boto3 is available
                use_s3 = boto3 and hasattr(settings, 'STORAGE_BACKEND') and settings.STORAGE_BACKEND == 's3' and hasattr(settings, 'AWS_S3_BUCKET') and settings.AWS_S3_BUCKET
                
                if use_s3:
                    try:
                        s3 = boto3.client('s3',
                                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                          region_name=settings.AWS_REGION)
                        video.file.seek(0)
                        s3.upload_fileobj(video.file, settings.AWS_S3_BUCKET, f"videos/{file_name}", ExtraArgs={'ACL': 'public-read'})
                        segment.video_url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/videos/{file_name}"
                        print(f"Uploaded video to S3: {segment.video_url}")
                        file_path_for_transcription = segment.video_url
                    except Exception as e:
                        print(f"S3 Upload Error: {e}")
                        raise HTTPException(status_code=500, detail=f"S3 Upload Failed: {str(e)}")
                else:
                    # Local Save
                    file_path = os.path.join(UPLOAD_DIR, file_name)
                    video.file.seek(0)
                    contents = await video.read()
                    with open(file_path, "wb") as f:
                        f.write(contents)
                    segment.video_url = f"/uploads/batch1/{file_name}"
                    file_path_for_transcription = file_path
                
                segment.content_type = 'video'
                segment.youtube_url = None
                video_uploaded = True
            elif segment.video_url and not video:
                # Keep existing video_url
                if segment.video_url.startswith("/uploads/batch1/"):
                    file_path_for_transcription = os.path.join(BACKEND_ROOT, segment.video_url.lstrip('/'))
                else:
                    file_path_for_transcription = segment.video_url
            elif youtube_url:
                # 2. YouTube URL
                segment.youtube_url = youtube_url
                segment.content_type = 'youtube'
                segment.video_url = None
            
            # 3. PDF Upload
            PDF_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "pdfs")
            os.makedirs(PDF_UPLOAD_DIR, exist_ok=True)

            current_pdfs_list = []
            if segment.pdf_files:
                try:
                    current_pdfs_list = json.loads(segment.pdf_files)
                except json.JSONDecodeError:
                    print(f"Error decoding existing pdf_files for {key}")
                    current_pdfs_list = []
            
            # Handle preserved PDFs
            final_pdf_list = []
            if preserved_pdf_data:
                try:
                    preserved_list = json.loads(preserved_pdf_data)
                    preserved_urls = {p.get('url') for p in preserved_list if p.get('url')}
                    final_pdf_list = [p for p in current_pdfs_list if p.get('url') in preserved_urls]
                except Exception as e:
                    print(f"Error parsing preserved_pdf_data: {e}")
                    final_pdf_list = current_pdfs_list
            else:
                final_pdf_list = current_pdfs_list

            new_pdfs_uploaded = []
            if pdf_files:
                segment.content_type = 'pdf'
                segment.video_url = None
                segment.youtube_url = None

                for idx, pdf in enumerate(pdf_files):
                    if pdf.filename:
                        file_ext = os.path.splitext(pdf.filename)[1]
                        unique_name = f"c{cycle_id}_d{day_number}_p{part_number}_s{segment_number}_pdf{idx}_{uuid.uuid4().hex[:6]}{file_ext}"
                        pdf_url = ""
                        local_pdf_path = None

                        # Check if S3 is configured
                        use_s3 = boto3 and hasattr(settings, 'STORAGE_BACKEND') and settings.STORAGE_BACKEND == 's3' and hasattr(settings, 'AWS_S3_BUCKET') and settings.AWS_S3_BUCKET
                        
                        if use_s3:
                            try:
                                s3 = boto3.client('s3',
                                                  aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                                  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                                  region_name=settings.AWS_REGION)
                                pdf.file.seek(0)
                                s3.upload_fileobj(pdf.file, settings.AWS_S3_BUCKET, f"pdfs/{unique_name}", ExtraArgs={'ACL': 'public-read'})
                                pdf_url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/pdfs/{unique_name}"
                                print(f"Uploaded PDF to S3: {pdf_url}")
                            except Exception as e:
                                print(f"S3 Upload Failed for PDF: {e}")
                                raise HTTPException(status_code=500, detail=f"S3 Upload Failed: {str(e)}")
                        else:
                            # Local Save
                            dest_path = os.path.join(PDF_UPLOAD_DIR, unique_name)
                            pdf.file.seek(0)
                            content = await pdf.read()
                            with open(dest_path, "wb") as f:
                                f.write(content)
                            pdf_url = f"/uploads/batch1/pdfs/{unique_name}"
                            local_pdf_path = dest_path

                        # Trigger PDF processing for first PDF
                        if idx == 0:
                            print(f"Triggering PDF processing for {key}")
                            current_pdf_name = pdf_names[idx] if pdf_names and idx < len(pdf_names) else pdf.filename
                            
                            # DECOUPLED PROCESSING: Capture task to run AFTER commit
                            if local_pdf_path:
                                # Local file - process directly
                                pending_pdf_task = (key, local_pdf_path, current_pdf_name)
                            elif pdf_url.startswith("https://"):
                                # S3 file - download to temp and process
                                try:
                                    # Create temp file but don't delete yet
                                    tmp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                                    print(f"Downloading S3 PDF to temp: {pdf_url}")
                                    urllib.request.urlretrieve(pdf_url, tmp_file.name)
                                    tmp_file.close() # Close handle
                                    
                                    pending_pdf_task = (key, tmp_file.name, current_pdf_name)
                                    pending_cleanup_file = tmp_file.name
                                except Exception as e:
                                    print(f"Error preparing S3 PDF for processing: {e}")

                        new_pdfs_uploaded.append({
                            "name": pdf_names[idx] if pdf_names and idx < len(pdf_names) else pdf.filename,
                            "url": pdf_url,
                            "order": len(final_pdf_list) + idx + 1
                        })

                # Append new PDFs to final list
                final_pdf_list.extend(new_pdfs_uploaded)

            if final_pdf_list:
                segment.pdf_files = json.dumps(final_pdf_list)
            
            # Commit to Database
            # Flush first to ensure data is written.
            db.flush()
            saved_video_url = segment.video_url
            saved_id = segment.id
            db.commit()
            
            # NO db.refresh(segment) needed as we don't access segment again
            
            response_data = {
                "success": True,
                "message": f"Segment {segment_number} saved successfully",
                "segment_key": key,
                "video_url": saved_video_url,
                "pdf_count": len(final_pdf_list),
                "id": saved_id 
            }
        
        # --- END OF DATABASE SESSION ---
        
        # Now run potentially long-running processing tasks on a separate session/connection
        if pending_pdf_task:
            print(f"Executing pending PDF task: {pending_pdf_task[0]}")
            try:
                await process_pdf_document(*pending_pdf_task)
            except Exception as e:
                print(f"PDF Processing Background Error: {e}")
                # We log but don't fail the request because upload succeeded
                import traceback
                traceback.print_exc()
            
            # Cleanup
            if pending_cleanup_file and os.path.exists(pending_cleanup_file):
                try:
                    os.unlink(pending_cleanup_file)
                except:
                    pass

        return response_data

    except Exception as e:
        print(f"Error saving segment: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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
