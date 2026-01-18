from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

# DevelopmentLog removed to avoid conflict with app.models.development_history
# Use app.models.development_history.DevelopmentLog instead

class DailySummary(Base):
    """Daily aggregated metrics for AI strategic planning."""
    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True, server_default=func.now())
    
    # Aggregated metrics
    active_students = Column(Integer, default=0)
    total_study_minutes = Column(Integer, default=0)
    avg_sentiment_score = Column(Float, default=0.0)
    security_alerts_count = Column(Integer, default=0)
    
    # JSON blob for portal-specific deep dives
    portal_health = Column(JSON, nullable=True) # {"admin": "good", "student": "sluggish"}
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
