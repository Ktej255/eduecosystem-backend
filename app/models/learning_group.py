"""
Social Learning Groups - Database Models
Enables collaborative learning experiences
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.session import Base


class GroupType(str, enum.Enum):
    STUDY = "study"
    PROJECT = "project"
    DISCUSSION = "discussion"
    PEER_SUPPORT = "peer_support"


class HouseType(str, enum.Enum):
    ALPHA = "alpha"  # For top performers
    BETA = "beta"   # For consistent learners
    GAMMA = "gamma"  # For active discussers
    DELTA = "delta"  # For new explorers


class GroupPrivacy(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    INVITE_ONLY = "invite_only"


class LearningGroup(Base):
    __tablename__ = "learning_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    group_type = Column(Enum(GroupType), default=GroupType.STUDY)
    privacy = Column(Enum(GroupPrivacy), default=GroupPrivacy.PUBLIC)

    # Optional course association
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)

    # Group settings
    max_members = Column(Integer, default=50)
    is_active = Column(Boolean, default=True)

    # Creator
    created_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Competitive Stats (Wolf Packs)
    house_type = Column(Enum(HouseType), nullable=True)
    pack_points = Column(Integer, default=0)
    weekly_points = Column(Integer, default=0)
    pack_metadata = Column(Text, nullable=True) # JSON for emblem, motto, colors

    # Relationships
    course = relationship("Course", back_populates="learning_groups")
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship(
        "GroupMembership", back_populates="group", cascade="all, delete-orphan"
    )
    posts = relationship(
        "GroupPost", back_populates="group", cascade="all, delete-orphan"
    )


class MemberRole(str, enum.Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"


class GroupMembership(Base):
    __tablename__ = "group_memberships"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("learning_groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum(MemberRole), default=MemberRole.MEMBER)

    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group = relationship("LearningGroup", back_populates="members")
    user = relationship("User")


class GroupPost(Base):
    __tablename__ = "group_posts"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("learning_groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    content = Column(Text, nullable=False)
    is_pinned = Column(Boolean, default=False)

    # Engagement
    likes_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    group = relationship("LearningGroup", back_populates="posts")
    author = relationship("User")
    comments = relationship(
        "GroupPostComment", back_populates="post", cascade="all, delete-orphan"
    )


class GroupPostComment(Base):
    __tablename__ = "group_post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("group_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("GroupPost", back_populates="comments")
    author = relationship("User")
