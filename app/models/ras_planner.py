from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class RASTopicProgress(Base):
    __tablename__ = "ras_topic_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic_id = Column(String, nullable=False, index=True) # e.g. "rg_01"
    
    completed = Column(Boolean, default=False)
    hours_spent = Column(Float, default=0.0)
    
    completed_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Store recall/summary data for AI evaluation later
    summary_text = Column(String, nullable=True)
    mastery_level = Column(Integer, default=0) # 0-100 scale

    # Relationships
    user = relationship("User", backref="ras_progress")
