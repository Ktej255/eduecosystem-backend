from typing import Any, List
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import models
from app.api import deps
from app.models.voice_note import VoiceNote
from app.schemas.voice_note import (
    VoiceNote as VoiceNoteSchema,
    VoiceNoteCreate,
    VoiceNoteUpdate,
)

router = APIRouter()

# Directory for storing voice notes
VOICE_NOTES_DIR = "uploads/voice_notes"


@router.post("/upload", response_model=VoiceNoteSchema)
async def upload_voice_note(
    file: UploadFile = File(...),
    lead_id: int = Form(None),
    field_activity_id: int = Form(None),
    title: str = Form(None),
    duration_seconds: int = Form(None),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload a voice note file.
    """
    # Validate file type
    allowed_types = ["audio/webm", "audio/mp3", "audio/mpeg", "audio/wav", "audio/ogg", "audio/m4a"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    # Create directory if it doesn't exist
    os.makedirs(VOICE_NOTES_DIR, exist_ok=True)
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if file.filename else "webm"
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(VOICE_NOTES_DIR, unique_filename)
    
    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create voice note record
    voice_note = VoiceNote(
        user_id=current_user.id,
        lead_id=lead_id,
        field_activity_id=field_activity_id,
        file_url=f"/uploads/voice_notes/{unique_filename}",
        file_name=file.filename,
        file_size_bytes=len(content),
        duration_seconds=duration_seconds,
        title=title
    )
    
    db.add(voice_note)
    db.commit()
    db.refresh(voice_note)
    return voice_note


@router.post("/", response_model=VoiceNoteSchema)
def create_voice_note(
    *,
    db: Session = Depends(deps.get_db),
    note_data: VoiceNoteCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a voice note record (when file is already uploaded separately).
    """
    voice_note = VoiceNote(
        user_id=current_user.id,
        lead_id=note_data.lead_id,
        field_activity_id=note_data.field_activity_id,
        file_url=note_data.file_url,
        file_name=note_data.file_name,
        file_size_bytes=note_data.file_size_bytes,
        duration_seconds=note_data.duration_seconds,
        title=note_data.title
    )
    
    db.add(voice_note)
    db.commit()
    db.refresh(voice_note)
    return voice_note


@router.get("/lead/{lead_id}", response_model=List[VoiceNoteSchema])
def get_voice_notes_for_lead(
    lead_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get voice notes for a specific lead.
    """
    notes = db.query(VoiceNote).filter(
        VoiceNote.lead_id == lead_id
    ).order_by(VoiceNote.created_at.desc()).all()
    
    return notes


@router.get("/my-notes", response_model=List[VoiceNoteSchema])
def get_my_voice_notes(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """
    Get current user's voice notes.
    """
    notes = db.query(VoiceNote).filter(
        VoiceNote.user_id == current_user.id
    ).order_by(VoiceNote.created_at.desc()).offset(skip).limit(limit).all()
    
    return notes


@router.put("/{id}", response_model=VoiceNoteSchema)
def update_voice_note(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    update_data: VoiceNoteUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a voice note.
    """
    note = db.query(VoiceNote).filter(VoiceNote.id == id).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Voice note not found")
    
    if note.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to update this voice note")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(note, field, value)
    
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{id}")
def delete_voice_note(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a voice note.
    """
    note = db.query(VoiceNote).filter(VoiceNote.id == id).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Voice note not found")
    
    if note.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete this voice note")
    
    # Delete file if exists
    if note.file_url:
        file_path = note.file_url.lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.delete(note)
    db.commit()
    
    return {"message": "Voice note deleted successfully"}
