from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class HandwritingSubmission(Base):
    __tablename__ = "handwriting_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    image_url = Column(String, nullable=False)

    # Self-Assessment Quiz Answers (stored as JSON string for MVP simplicity)
    quiz_data = Column(Text, nullable=True)

    # Analysis Report
    report_content = Column(Text, nullable=True)
    report_level = Column(Integer, default=1)  # 1=Free, 2=Paid, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="submissions")
