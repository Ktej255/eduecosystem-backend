"""
Achievement System Models

Defines achievements that users can unlock through various actions.
Achievements award coins and provide motivation for engagement.
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
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class AchievementCategory(str, enum.Enum):
    """Categories of achievements"""

    LEARNING = "learning"  # Course/lesson completions
    MASTERY = "mastery"  # Perfect quiz scores, high grades
    SOCIAL = "social"  # Reviews, discussions, interactions
    STREAK = "streak"  # Daily streak maintenance
    EXPLORER = "explorer"  # Trying new features
    DEDICATED = "dedicated"  # Long-term commitment
    SPECIAL = "special"  # Limited-time or hidden achievements


class AchievementRarity(str, enum.Enum):
    """Rarity tiers for achievements"""

    COMMON = "common"  # Easy to unlock
    RARE = "rare"  # Moderate difficulty
    EPIC = "epic"  # Challenging
    LEGENDARY = "legendary"  # Very rare/difficult


class Achievement(Base):
    """
    Predefined achievements that users can unlock.
    Each achievement has unlock conditions and coin rewards.
    """

    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Categorization
    category = Column(SQLEnum(AchievementCategory), nullable=False, index=True)
    rarity = Column(SQLEnum(AchievementRarity), default=AchievementRarity.COMMON)

    # Visual
    icon = Column(String(50), default="trophy")  # Icon name/emoji

    # Rewards
    coin_reward = Column(Integer, default=50)

    # Unlock conditions (JSON format)
    # Examples:
    # {"type": "quiz_count", "count": 1}
    # {"type": "perfect_quiz_count", "count": 1}
    # {"type": "course_complete_count", "count": 1}
    # {"type": "streak_days", "days": 7}
    unlock_condition = Column(JSON, nullable=False)

    # Visibility
    is_hidden = Column(Boolean, default=False)  # Hidden until unlocked
    is_active = Column(Boolean, default=True)  # Can be temporarily disabled

    # Ordering
    display_order = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user_achievements = relationship(
        "UserAchievement", back_populates="achievement", cascade="all, delete-orphan"
    )


class UserAchievement(Base):
    """
    Tracks which achievements each user has unlocked.
    Includes progress for multi-step achievements.
    """

    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    achievement_id = Column(
        Integer,
        ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Progress tracking (0.0 to 1.0, where 1.0 = complete)
    progress = Column(Integer, default=100)  # Percentage (0-100)

    # Unlock timestamp
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Notification status
    notified = Column(Boolean, default=False)  # Whether user was notified

    # Relationships
    user = relationship("User", back_populates="achievements_earned")
    achievement = relationship("Achievement", back_populates="user_achievements")

    # Unique constraint: each user can only unlock each achievement once
    __table_args__ = ({"sqlite_autoincrement": True},)
