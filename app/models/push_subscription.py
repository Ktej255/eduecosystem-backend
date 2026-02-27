from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Browser Endpoint URL
    endpoint = Column(String, nullable=False, unique=True, index=True)
    
    # VAPID Keys
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
