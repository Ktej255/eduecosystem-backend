
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Batch1Segment(Base):
    __tablename__ = "batch1_segments"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, nullable=False)
    day_number = Column(Integer, nullable=False)
    part_number = Column(Integer, nullable=False)
    segment_number = Column(Integer, nullable=False)
    
    # Composite key as string for easier lookups: "1_1_1_1"
    segment_key = Column(String, unique=True, index=True, nullable=False)
    
    title = Column(String, nullable=False)
    video_url = Column(String, nullable=True)
    
    # Transcription / Content
    transcription_text = Column(String, nullable=True)  # Full text or link to file
    key_points = Column(String, nullable=True) # JSON list or text
    
    # Status
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('segment_key', name='uq_batch1_segment_key'),
    )
