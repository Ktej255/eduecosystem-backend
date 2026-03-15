from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base

class UserActivitySession(Base):
    __tablename__ = "user_activity_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_heartbeat = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    
    duration_seconds = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    user = relationship("User", backref="user_activity_sessions")
