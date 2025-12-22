from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from app.db.session import Base
from datetime import datetime


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String, nullable=False)
    description = Column(Text)

    # Ordering
    order_index = Column(Integer, default=0, index=True)

    # Module-level quiz (optional)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=True)

    # Assignment prompts for this module
    assignment_prompts = Column(JSON, default=list)  # List of assignment descriptions

    # Metadata
    duration_minutes = Column(Integer, default=0)  # Total duration of all lessons
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="modules")
    lessons = relationship(
        "Lesson",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Lesson.order_index",
    )
    module_quiz = relationship("Quiz", foreign_keys=[quiz_id])

    def __repr__(self):
        return f"<Module {self.title}>"
