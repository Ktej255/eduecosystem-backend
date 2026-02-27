from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class StudentReport(Base):
    __tablename__ = "student_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # "saturday_test", "chapter_test", "activity_log", "mood_log", "boarding", "streaks"
    report_type = Column(String, index=True, nullable=False)
    
    # Acts as a unique idempotent key to prevent duplicates (e.g., "batch11_saturday_v2_1")
    report_key = Column(String, index=True, nullable=False)
    
    # The actual JSON payload from the frontend
    data = Column(JSON, nullable=True)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User", back_populates="student_reports")
