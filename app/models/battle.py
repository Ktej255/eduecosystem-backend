from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base

class BattleStatus(str, enum.Enum):
    PENDING = "pending"   # Challenger created, waiting for Defender
    ACTIVE = "active"     # Defender accepted (or synchronous start)
    COMPLETED = "completed"
    EXPIRED = "expired"

class PackBattle(Base):
    __tablename__ = "pack_battles"

    id = Column(Integer, primary_key=True, index=True)
    
    # Participants
    challenger_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    defender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Metadata
    status = Column(Enum(BattleStatus), default=BattleStatus.PENDING)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Content
    # JSON list of question IDs or full question objects used in this battle
    questions_data = Column(JSON, nullable=False) 
    
    # Scores
    challenger_score = Column(Integer, default=0)
    defender_score = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    challenger = relationship("User", foreign_keys=[challenger_id])
    defender = relationship("User", foreign_keys=[defender_id])
    winner = relationship("User", foreign_keys=[winner_id])

