from typing import Any, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models
from app.api import deps
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/upload-url", response_model=Dict[str, str])
def get_video_upload_url(
    lesson_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a signed upload URL for video uploading.
    For now, this returns a mock URL for local testing.
    """
    # Verify lesson exists and user is instructor
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check if user is the instructor of the course
    # (Assuming we have access to course via module -> lesson)
    # simplified check for now

    # Generate a unique video ID
    video_id = str(uuid.uuid4())

    # Update lesson with video ID and status
    lesson.video_id = video_id
    lesson.video_provider = "local"  # or "cloudflare"
    lesson.video_status = "uploading"
    db.commit()

    return {
        "upload_url": f"https://api.example.com/upload/{video_id}",
        "video_id": video_id,
    }


class VideoLinkRequest(BaseModel):
    lesson_id: int
    youtube_url: str

@router.post("/link")
def link_youtube_video(
    link_data: VideoLinkRequest,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Link a YouTube video to a lesson.
    """
    lesson = db.query(models.Lesson).filter(models.Lesson.id == link_data.lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Update lesson
    lesson.video_url = link_data.youtube_url
    lesson.video_provider = "youtube"
    lesson.video_status = "ready"
    lesson.video_uploaded_at = datetime.utcnow()
    
    db.commit()
    
    return {"status": "success", "video_url": lesson.video_url}


@router.post("/{video_id}/status")
def update_video_status(
    video_id: str,
    status: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Manually update video status (for testing).
    """
    lesson = db.query(models.Lesson).filter(models.Lesson.video_id == video_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Video not found")

    lesson.video_status = status
    if status == "ready":
        lesson.video_uploaded_at = datetime.utcnow()
        # Set a mock video URL
        lesson.video_url = f"https://example.com/videos/{video_id}/manifest.m3u8"
        lesson.video_thumbnail_url = (
            f"https://example.com/videos/{video_id}/thumbnail.jpg"
        )

    db.commit()
    return {"status": "success"}


@router.get("/{video_id}/status", response_model=Dict[str, str])
def get_video_status(
    video_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current processing status of a video.
    """
    lesson = db.query(models.Lesson).filter(models.Lesson.video_id == video_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "status": lesson.video_status,
        "video_url": lesson.video_url,
        "thumbnail_url": lesson.video_thumbnail_url,
    }
