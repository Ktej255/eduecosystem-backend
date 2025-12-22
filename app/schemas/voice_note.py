from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class VoiceNoteBase(BaseModel):
    """Base schema for voice note."""
    lead_id: Optional[int] = None
    field_activity_id: Optional[int] = None
    title: Optional[str] = None


class VoiceNoteCreate(VoiceNoteBase):
    """Schema for creating a voice note (file is uploaded separately)."""
    file_url: str
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[int] = None


class VoiceNoteUpdate(BaseModel):
    """Schema for updating a voice note."""
    title: Optional[str] = None
    transcription: Optional[str] = None


class VoiceNote(VoiceNoteBase):
    """Schema for returning a voice note."""
    id: int
    user_id: int
    file_url: str
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[int] = None
    transcription: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoiceNoteUploadResponse(BaseModel):
    """Response after uploading a voice note file."""
    voice_note: VoiceNote
    upload_url: str
