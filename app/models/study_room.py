from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base


class StudyRoom(Base):
    __tablename__ = "study_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    topic = Column(String)
    participants_count = Column(Integer, default=0)
    thumbnail_url = Column(String, nullable=True)

    # Relationships
    chat_messages = relationship(
        "RealtimeChatMessage", back_populates="study_room", cascade="all, delete-orphan"
    )
