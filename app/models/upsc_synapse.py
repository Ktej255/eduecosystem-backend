import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

class UPSCCognitiveProfile(Base):
    """
    Stores the high-level cognitive state of a student for the UPSC Synapse Engine.
    Tracks Adaptive Level (1-3), Stress Index, and overall Weighted Proficiency Score (WPS).
    """
    __tablename__ = "upsc_cognitive_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    current_level = Column(String, default="level1") # level1, level2, level3
    wps_score = Column(Float, default=0.0) # Weighted Proficiency Score (0-100)
    stress_index = Column(Float, default=0.0) # 0-10 scale
    
    # Unlock Status
    is_level2_unlocked = Column(Boolean, default=False)
    is_level3_unlocked = Column(Boolean, default=False)
    
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="upsc_synapse_profile")
    gap_analysis = relationship("UPSCGapAnalysis", back_populates="profile", cascade="all, delete-orphan")
    unlock_transactions = relationship("UPSCUnlockTransaction", back_populates="profile", cascade="all, delete-orphan")


class UPSCGapAnalysis(Base):
    """
    Detailed gap analysis per chapter/topic.
    Maps to the Red/Yellow/Green heatmap.
    """
    __tablename__ = "upsc_gap_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("upsc_cognitive_profiles.id"), nullable=False)
    
    chapter_id = Column(Integer, nullable=False)
    subject = Column(String, default="Polity")
    
    status = Column(String, default="unattempted") # unattempted, knowledge_gap (Red), logic_gap (Yellow), mastered (Green)
    recall_accuracy = Column(Float, default=0.0)
    last_tested_at = Column(DateTime, default=datetime.utcnow)
    
    # Granular details for "Deep Audit"
    gap_details = Column(JSON, nullable=True) # { "missingParameters": ["Article 21"], "suggestedPage": 42 }

    profile = relationship("UPSCCognitiveProfile", back_populates="gap_analysis")


class UPSCUnlockTransaction(Base):
    """
    Tracks micro-transactions for unlocking levels.
    """
    __tablename__ = "upsc_unlock_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("upsc_cognitive_profiles.id"), nullable=False)
    
    level_unlocked = Column(String, nullable=False) # level2, level3
    amount_paid = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    transaction_id = Column(String, nullable=True) # Payment Gateway ID
    status = Column(String, default="completed")
    
    unlocked_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("UPSCCognitiveProfile", back_populates="unlock_transactions")
