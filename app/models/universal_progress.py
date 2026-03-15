from sqlalchemy import Column, Integer, ForeignKey, DateTime, text, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class UniversalProgress(Base):
    __tablename__ = "universal_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    state_blob = Column(JSON, nullable=False)
    last_synced_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))

    user = relationship("User", backref="universal_state")
