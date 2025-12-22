"""
Challenge System Models

Defines daily/weekly challenges for user engagement.
Challenges have time limits and reward users for completion.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    Enum as SQLEnum,
    JSON,
    Date,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class ChallengeType(str, enum.Enum):
    """Types of challenges based on duration"""

    DAILY = "daily"  # 24-hour challenges
    WEEKLY = "weekly"  # 7-day challenges
    SPECIAL = "special"  # Limited-time events


class Challenge(Base):
    """
    Challenges that users can complete for rewards.
    New challenges are generated periodically (daily/weekly).
    """

    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Type and timing
    type = Column(SQLEnum(ChallengeType), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    # Requirements (JSON format)
    # Examples:
    # {"type": "complete_lessons", "count": 3}
    # {"type": "quiz_score", "min_score": 80, "count": 1}
    # {"type": "discussion_posts", "count": 2}
    requirement = Column(JSON, nullable=False)

    # Rewards
    reward_coins = Column(Integer, default=50)
    reward_achievement_id = Column(
        Integer, ForeignKey("achievements.id"), nullable=True
    )  # Optional achievement reward

    # Status
    is_active = Column(Boolean, default=True)

    # Difficulty indicator (1-5)
    difficulty = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_challenges = relationship(
        "UserChallenge", back_populates="challenge", cascade="all, delete-orphan"
    )
    reward_achievement = relationship("Achievement")


class UserChallenge(Base):
    """
    Tracks each user's progress on active challenges.
    """

    __tablename__ = "user_challenges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    challenge_id = Column(
        Integer,
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Progress tracking (JSON to store detailed progress)
    # Example: {"lessons_completed": 2, "target": 3}
    progress_data = Column(JSON, default=dict)

    # Progress percentage (0-100)
    progress_percentage = Column(Integer, default=0)

    # Completion
    completed_at = Column(DateTime(timezone=True), nullable=True)
    reward_claimed = Column(Boolean, default=False)
    claimed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    # user = relationship("User", back_populates="challenges_active")
    challenge = relationship("Challenge", back_populates="user_challenges")

    # Unique constraint: each user can only have one instance of each challenge
    __table_args__ = ({"sqlite_autoincrement": True},)
