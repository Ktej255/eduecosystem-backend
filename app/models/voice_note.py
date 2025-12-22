from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class VoiceNote(Base):
    """Model for voice note recordings attached to leads or activities."""
    __tablename__ = "voice_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Optional associations
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    field_activity_id = Column(Integer, ForeignKey("field_activities.id"), nullable=True, index=True)
    
    # File details
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Transcription (optional, for AI processing later)
    transcription = Column(Text, nullable=True)
    
    # Metadata
    title = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="voice_notes")
    lead = relationship("Lead", back_populates="voice_notes")
    field_activity = relationship("FieldActivity", back_populates="voice_notes")
