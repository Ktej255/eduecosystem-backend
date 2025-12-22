"""
Batch 1 Content API Endpoints
Manage video segments for UPSC Prelims Batch 1 course
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
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
    duration: str = "25:00"


class SegmentResponse(BaseModel):
    """Response for segment data"""
    id: int
    title: str
    key_points: str
    video_url: Optional[str]
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
                duration=data.get("duration", "25:00")
            ))
        else:
            # Default segment if not uploaded
            segments.append(SegmentResponse(
                id=seg_num,
                title=f"Segment {seg_num} (Not Uploaded)",
                key_points="Key points will appear here after admin uploads content",
                video_url=None,
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
    key_points: str = Form(""),  # Made optional with default empty string
    video: Optional[UploadFile] = File(None)
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
        
        # Store segment data
        SEGMENTS_STORE[key] = {
            "title": title,
            "key_points": key_points,
            "video_url": video_url,
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
