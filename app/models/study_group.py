"""Study Group models for collaborative learning"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Table,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base

# Association table for group members
group_members = Table(
    "group_members",
    Base.metadata,
    Column(
        "group_id",
        Integer,
        ForeignKey("study_groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("joined_at", DateTime, default=datetime.utcnow),
)


class StudyGroup(Base):
    """Model for study groups"""

    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    creator_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_private = Column(Boolean, default=False)
    max_members = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", backref="created_groups")
    # members = relationship("User", secondary=group_members, backref="study_groups")
    chat_messages = relationship(
        "RealtimeChatMessage",
        back_populates="study_group",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<StudyGroup {self.name}>"
