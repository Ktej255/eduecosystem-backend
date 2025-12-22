from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class FieldActivity(Base):
    """Model for tracking field agent activities like check-ins, check-outs, meetings, and visits."""
    __tablename__ = "field_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Activity type: CHECK_IN, CHECK_OUT, MEETING, VISIT, WALK_IN, EVENT, CAMPUS_VISIT
    activity_type = Column(String(50), nullable=False, index=True)
    
    # Location data
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    
    # Optional lead association
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    
    # Activity details
    title = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    photos = Column(JSON, nullable=True)  # Array of photo URLs
    
    # Duration tracking (for meetings/visits)
    duration_minutes = Column(Integer, nullable=True)
    
    # Route tracking
    route_distance_km = Column(Float, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="field_activities")
    lead = relationship("Lead", back_populates="field_activities")
    voice_notes = relationship("VoiceNote", back_populates="field_activity")
