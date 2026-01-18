from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class BatchSentiment(Base):
    """Aggregated sentiment for a specific cohort/batch over time"""
    __tablename__ = "batch_sentiments"

    id = Column(Integer, primary_key=True, index=True)
    batch_name = Column(String, index=True)  # e.g., "Batch 1.1", "Corporate-A"
    date = Column(Date, index=True)
    
    # Sentiment scores (0.0 to 1.0)
    focused_score = Column(Float, default=0.0)
    anxious_score = Column(Float, default=0.0)
    tired_score = Column(Float, default=0.0)
    inspired_score = Column(Float, default=0.0)
    
    # Dominant vibe
    dominant_vibe = Column(String)  # e.g., "Focused", "Anxious"
    
    # Metadata
    sample_size = Column(Integer, default=0)  # Number of reflections aggregated
    top_keywords = Column(String)  # Comma-separated or JSON string of common keywords
    
    created_at = Column(DateTime, default=datetime.utcnow)
