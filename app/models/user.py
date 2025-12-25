from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.permissions import user_roles


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    full_name = Column(String, index=True)
    coins = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    token_version = Column(Integer, default=1)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True, index=True)
    group = relationship("Group", back_populates="members")

    # Admin fields
    role = Column(String, default="student", index=True)  # student, admin
    last_login = Column(DateTime, nullable=True)
    is_banned = Column(Boolean, default=False)
    email_notifications = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=True)  # Students auto-approved, teachers/admins need approval

    # Subscription fields
    is_premium = Column(Boolean, default=False)
    stripe_customer_id = Column(String, nullable=True)
    subscription_status = Column(
        String, default="free"
    )  # free, active, past_due, canceled

    # Organization (for Enterprise SSO)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_sso_user = Column(Boolean, default=False)
    sso_external_id = Column(String, nullable=True, index=True)
    is_verified = Column(Boolean, default=False)

    # Subscription Relationship
    subscription = relationship("UserSubscription", back_populates="user")

    # Core Relationships
    tasks = relationship("Task", back_populates="owner")
    submissions = relationship("HandwritingSubmission", back_populates="owner")
    meditation_sessions = relationship(
        "MeditationSession", back_populates="owner", cascade="all, delete-orphan"
    )
    activity_logs = relationship(
        "ActivityLog", back_populates="user", cascade="all, delete-orphan"
    )
    rewards = relationship(
        "UserReward", back_populates="user", cascade="all, delete-orphan"
    )

    # LMS Relationships
    courses_taught = relationship("Course", back_populates="instructor")
    enrollments = relationship(
        "Enrollment", back_populates="user", cascade="all, delete-orphan"
    )
    course_payments = relationship(
        "CoursePayment", back_populates="user", cascade="all, delete-orphan"
    )
    certificates = relationship(
        "Certificate", back_populates="user", cascade="all, delete-orphan"
    )
    quiz_attempts = relationship(
        "QuizAttempt", back_populates="user", cascade="all, delete-orphan"
    )
    assignment_submissions = relationship(
        "Submission", back_populates="user", cascade="all, delete-orphan"
    )

    # Bundle Relationships
    bundles = relationship("CourseBundle", back_populates="instructor")
    bundle_enrollments = relationship("BundleEnrollment", back_populates="user")

    # Notifications
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    # Chatbot Relationships
    chat_sessions = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )

    # Preferences
    preferences = relationship(
        "UserPreference", back_populates="user", cascade="all, delete-orphan"
    )

    # Chat and Presence
    realtime_chat_messages = relationship(
        "RealtimeChatMessage", back_populates="sender", cascade="all, delete-orphan"
    )
    presence = relationship(
        "RealtimeUserPresence",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Roles (RBAC System)
    roles = relationship("Role", secondary=user_roles, back_populates="users")

    # AI Conversations
    ai_conversations = relationship(
        "AIConversation", back_populates="user", cascade="all, delete-orphan"
    )

    # Email Preferences
    email_preferences = relationship(
        "UserEmailPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Gamification (Advanced)
    achievements_earned = relationship(
        "UserAchievement",
        foreign_keys="UserAchievement.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # challenges_active = relationship("UserChallenge", foreign_keys="UserChallenge.user_id", back_populates="user", cascade="all, delete-orphan")
    # coin_transactions = relationship("CoinTransaction", foreign_keys="CoinTransaction.user_id", back_populates="user", cascade="all, delete-orphan")

    # Two-Factor Authentication
    two_factor_auth = relationship(
        "TwoFactorAuth",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    backup_codes = relationship(
        "TwoFactorBackupCode", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def is_2fa_enabled(self) -> bool:
        """Check if user has Two-Factor Authentication enabled"""
        return self.two_factor_auth is not None and self.two_factor_auth.is_enabled

    # AI Avatars
    ai_avatars = relationship("AIAvatar", back_populates="user", cascade="all, delete-orphan")

    # Graphotherapy Progress
    graphotherapy_progress = relationship(
        "GraphotherapyProgress",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Meditation Progress
    meditation_progress = relationship(
        "MeditationProgress",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Organization (for Enterprise SSO)
    organization = relationship("Organization", back_populates="users")

    # Lead Management
    leads = relationship("Lead", back_populates="assigned_to")

    # Mobile CRM - Field Activities
    field_activities = relationship("FieldActivity", back_populates="user", cascade="all, delete-orphan")
    call_logs = relationship("CallLog", back_populates="user", cascade="all, delete-orphan")
    voice_notes = relationship("VoiceNote", back_populates="user", cascade="all, delete-orphan")

    # Retention System (FSRS-based knowledge decay tracking)
    topic_logs = relationship("UserTopicLog", back_populates="user", cascade="all, delete-orphan")

