"""
AI Avatar Model
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class AIAvatar(Base):
    """AI Avatar for automated assistance"""
    __tablename__ = "ai_avatars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Configuration
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    purpose = Column(String(50), nullable=False)  # sales, support, engage, generic
    
    # Personality
    personality = Column(Text, nullable=True)
    tone = Column(String(50), default="professional")  # professional, casual, friendly, formal
    response_style = Column(String(50), default="concise")  # concise, detailed, conversational
    
    # Knowledge Base (JSON field)
    knowledge_base = Column(JSON, default={})  # URLs, documents, instructions
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="ai_avatars")
