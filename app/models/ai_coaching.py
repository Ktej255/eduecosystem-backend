
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class CoachingSession(Base):
    __tablename__ = "ai_coaching_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic = Column(String, nullable=False)
    
    # Context context (e.g. which quiz was failed, what text was selected)
    context_data = Column(JSON, default={})
    
    # Valid JSON list of messages: [{"role": "user", "content": "..."}, ...]
    messages = Column(JSON, default=[])
    
    status = Column(String, default="active") # active, completed, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", backref="coaching_sessions")
