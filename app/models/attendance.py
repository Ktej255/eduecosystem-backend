from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_type = Column(String, index=True) # "morning_meditation", "night_class", etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_present = Column(Boolean, default=True)
    
    # Optional: Tracking join method (live vs recording could be inferred but explicit is nice)
    mode = Column(String, default="live") # "live" or "recording"

    user = relationship("User", back_populates="attendance_records")
