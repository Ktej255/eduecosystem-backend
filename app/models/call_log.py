from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class CallLog(Base):
    """Model for tracking phone calls made to leads."""
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Call details
    call_type = Column(String(20), nullable=False)  # OUTGOING, INCOMING, MISSED
    phone_number = Column(String(20), nullable=True)
    duration_seconds = Column(Integer, default=0)
    
    # Call outcome
    outcome = Column(String(50), nullable=True)  # CONNECTED, NO_ANSWER, BUSY, VOICEMAIL, WRONG_NUMBER
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    call_started_at = Column(DateTime(timezone=True), default=func.now())
    call_ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="call_logs")
    lead = relationship("Lead", back_populates="call_logs")
