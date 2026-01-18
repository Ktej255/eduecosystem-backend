from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class GhostLoginAlert(Base):
    """Flags suspicious login activity (e.g., account sharing across distances)"""
    __tablename__ = "ghost_login_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Details of conflicting logins
    login_a_ip = Column(String)
    login_a_time = Column(DateTime)
    login_b_ip = Column(String)
    login_b_time = Column(DateTime)
    
    # Distance/Risk metrics
    estimated_distance_km = Column(Float, nullable=True)
    time_difference_minutes = Column(Float)
    risk_score = Column(Integer)  # 1-10
    
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    admin_notes = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="ghost_alerts")
