from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import enum
from app.db.session import Base

class ChapterStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class PolityChapterTask(Base):
    __tablename__ = "polity_chapter_tasks"

    id = Column(Integer, primary_key=True, index=True)
    chapter_number = Column(Integer, unique=True, index=True, nullable=False)
    chapter_title = Column(String, nullable=False)
    
    # Simple boolean flags
    research_done = Column(Boolean, default=False)
    report_generated = Column(Boolean, default=False)
    report_saved = Column(Boolean, default=False)
    video_generated = Column(Boolean, default=False)
    podcast_generated = Column(Boolean, default=False)
    
    status = Column(String, default=ChapterStatus.PENDING)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
