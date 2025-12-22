from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class ShadowModeSession(Base):
    __tablename__ = "shadow_mode_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    day_number = Column(Integer)  # 1-7
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0)
    goals_completed = Column(Integer, default=0)
    total_goals = Column(Integer, default=0)
    focus_score = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationship
    user = relationship("User")
