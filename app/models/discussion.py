from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class DiscussionCategory(Base):
    """Discussion category for organizing threads within a course"""

    __tablename__ = "discussion_categories"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    course = relationship("Course", backref="discussion_categories")
    threads = relationship(
        "DiscussionThread", back_populates="category", cascade="all, delete-orphan"
    )


class DiscussionThread(Base):
    """Discussion thread/topic within a category"""

    __tablename__ = "discussion_threads"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(
        Integer, ForeignKey("discussion_categories.id"), nullable=False
    )
    course_id = Column(
        Integer, ForeignKey("courses.id"), nullable=False
    )  # Denormalized for easier queries
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)

    # Thread status
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)

    # Metrics
    view_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    category = relationship("DiscussionCategory", back_populates="threads")
    course = relationship("Course", backref="discussion_threads")
    author = relationship("User", foreign_keys=[user_id], backref="discussion_threads")
    posts = relationship(
        "DiscussionPost", back_populates="thread", cascade="all, delete-orphan"
    )


class DiscussionPost(Base):
    """Reply/post within a discussion thread"""

    __tablename__ = "discussion_posts"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("discussion_threads.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_post_id = Column(
        Integer, ForeignKey("discussion_posts.id"), nullable=True
    )  # For nested replies

    content = Column(Text, nullable=False)

    # Post status
    is_answer = Column(Boolean, default=False)  # Mark as accepted answer (for Q&A)
    is_edited = Column(Boolean, default=False)

    # Voting
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    thread = relationship("DiscussionThread", back_populates="posts")
    author = relationship("User", foreign_keys=[user_id], backref="discussion_posts")
    parent_post = relationship("DiscussionPost", remote_side=[id], backref="replies")
    votes = relationship(
        "PostVote", back_populates="post", cascade="all, delete-orphan"
    )


class PostVote(Base):
    """User votes on discussion posts"""

    __tablename__ = "post_votes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("discussion_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vote_type = Column(String(10), nullable=False)  # "upvote" or "downvote"

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    post = relationship("DiscussionPost", back_populates="votes")
    user = relationship("User", backref="post_votes")

    # Unique constraint: one vote per user per post
    __table_args__ = ({"sqlite_autoincrement": True},)
