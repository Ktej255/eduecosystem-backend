from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    phone = Column(String, index=True, nullable=True)
    status = Column(String, default="NEW")  # NEW, CONTACTED, INTERESTED, ENROLLED, CLOSED, JUNK
    
    # Source Attribution
    source_primary = Column(String, index=True, nullable=True)
    source_secondary = Column(String, nullable=True)
    source_tertiary = Column(String, nullable=True)
    
    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to = relationship("User", back_populates="leads")
    
    # Verification & Intent
    is_verified = Column(Boolean, default=False)
    verification_method = Column(String, nullable=True) # EMAIL, SMS, WHATSAPP
    intent_score = Column(Float, default=0.0)
    
    # Location (for geo-based lead allocation)
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    location_address = Column(String, nullable=True)
    
    # Details
    notes = Column(Text, nullable=True)
    last_activity = Column(DateTime(timezone=True), default=func.now())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Mobile CRM Relationships
    field_activities = relationship("FieldActivity", back_populates="lead")
    call_logs = relationship("CallLog", back_populates="lead")
    voice_notes = relationship("VoiceNote", back_populates="lead")
