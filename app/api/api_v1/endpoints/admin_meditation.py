"""
Meditation Session System - Admin API Endpoints
Manage meditation processes and upload videos
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os
import uuid

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.meditation import MeditationProcess
from app.schemas.meditation import (
    MeditationProcessCreate,
    MeditationProcessUpdate,
    MeditationProcessResponse,
)

router = APIRouter()

# Upload directory for meditation videos
UPLOAD_DIR = "uploads/meditation"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def require_admin(current_user: User = Depends(deps.get_current_user)) -> User:
    """Require admin user"""
    if current_user.role not in ["admin", "superadmin"] and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/processes", response_model=List[MeditationProcessResponse])
def get_all_processes(
    level: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get all meditation processes (optionally filtered by level)"""
    query = db.query(MeditationProcess)
    if level:
        query = query.filter(MeditationProcess.level == level)
    processes = query.order_by(MeditationProcess.level, MeditationProcess.order).all()
    return processes


@router.post("/processes", response_model=MeditationProcessResponse)
def create_process(
    process_in: MeditationProcessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new meditation process"""
    process = MeditationProcess(
        name=process_in.name,
        description=process_in.description,
        order=process_in.order,
        duration_minutes=process_in.duration_minutes,
        level=process_in.level,
        is_active=True
    )
    db.add(process)
    db.commit()
    db.refresh(process)
    return process


@router.get("/processes/{process_id}", response_model=MeditationProcessResponse)
def get_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get a specific meditation process"""
    process = db.query(MeditationProcess).filter(MeditationProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return process


@router.put("/processes/{process_id}", response_model=MeditationProcessResponse)
def update_process(
    process_id: int,
    process_in: MeditationProcessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a meditation process"""
    process = db.query(MeditationProcess).filter(MeditationProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    update_data = process_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(process, field, value)
    
    db.commit()
    db.refresh(process)
    return process


@router.delete("/processes/{process_id}")
def delete_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a meditation process"""
    process = db.query(MeditationProcess).filter(MeditationProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    db.delete(process)
    db.commit()
    return {"success": True, "message": "Process deleted"}


@router.post("/processes/{process_id}/video", response_model=MeditationProcessResponse)
async def upload_process_video(
    process_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Upload an explanation video for a meditation process"""
    process = db.query(MeditationProcess).filter(MeditationProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    # Validate file type
    allowed_types = ["video/mp4", "video/webm", "video/ogg", "video/quicktime"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".mp4"
    unique_filename = f"process_{process_id}_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Update process with video URL
    process.video_url = f"/uploads/meditation/{unique_filename}"
    process.video_filename = file.filename
    
    db.commit()
    db.refresh(process)
    
    return process


@router.delete("/processes/{process_id}/video")
def delete_process_video(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete the video for a meditation process"""
    process = db.query(MeditationProcess).filter(MeditationProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    # Delete file if exists
    if process.video_url:
        file_path = process.video_url.replace("/uploads/", "uploads/")
        if os.path.exists(file_path):
            os.remove(file_path)
    
    process.video_url = None
    process.video_filename = None
    
    db.commit()
    return {"success": True, "message": "Video deleted"}
