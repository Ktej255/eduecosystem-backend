from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class TaskType(str, enum.Enum):
    STUDY = "study"
    ASSIGNMENT = "assignment"
    VIDEO = "video"
    QUIZ = "quiz"
    GRAPHO = "grapho"
    MEDITATION = "meditation"
    EXERCISE = "exercise"
    OTHER = "other"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    task_type = Column(String, default=TaskType.OTHER)
    duration_minutes = Column(Integer, default=30)

    # For MVP: Master Schedule (assigned to all) or Personal (assigned to user)
    is_master = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Scheduling
    scheduled_date = Column(DateTime, index=True)
    is_completed = Column(Boolean, default=False)

    owner = relationship("User", back_populates="tasks")


# Add relationship to User model (need to update user.py later)
