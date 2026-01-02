
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
    # Content Details
    content_type = Column(String, default="video")  # video, youtube, pdf
    video_url = Column(String, nullable=True)
    youtube_url = Column(String, nullable=True)
    pdf_files = Column(String, nullable=True)  # JSON list of PDFs (name, url, order)
    
    # Transcription / Content
    transcription_text = Column(String, nullable=True)  # Full text or link to file
    pdf_data = Column(String, nullable=True)  # JSON blob of processed PDF pages (text/images)
    key_points = Column(String, nullable=True) # JSON list or text
    
    # Duration
    duration = Column(String, default="25:00")
    
    # Status
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('segment_key', name='uq_batch1_segment_key'),
    )

class Batch1TestResult(Base):
    __tablename__ = "batch1_test_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cycle_id = Column(Integer, nullable=False)
    day_number = Column(Integer, nullable=False)
    
    score = Column(Float, nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_count = Column(Integer, nullable=False)
    incorrect_count = Column(Integer, nullable=False)
    unanswered_count = Column(Integer, nullable=False)
    
    # Store answers as JSON: [{"qId": 1, "answer": 0, "isCorrect": true}, ...]
    answers_json = Column(String, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="batch1_test_results")
