from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.orm import relationship

from app.db.session import Base
from datetime import datetime
import enum
# Note: course_tags is a Table object, usually imported to avoid circular dependency issues,
# but here we use string reference in relationship to avoid import issues.


class CourseLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseCategory(str, enum.Enum):
    PROGRAMMING = "programming"
    DATA_SCIENCE = "data_science"
    DESIGN = "design"
    BUSINESS = "business"
    MARKETING = "marketing"
    PERSONAL_DEVELOPMENT = "personal_development"
    HEALTH = "health"
    LANGUAGE = "language"
    OTHER = "other"


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    slug = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text)
    long_description = Column(Text)
    thumbnail_url = Column(String, nullable=True)
    preview_video_url = Column(String, nullable=True)

    # Instructor
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Categorization
    # category = Column(SQLEnum(CourseCategory), default=CourseCategory.OTHER, index=True) # Deprecated
    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=True, index=True
    )

    level = Column(SQLEnum(CourseLevel), default=CourseLevel.BEGINNER, index=True)
    # tags = Column(JSON, default=list)  # Deprecated
    prerequisites = Column(JSON, default=list)  # List of string prerequisites

    # Status
    is_published = Column(Boolean, default=False, index=True)
    is_featured = Column(Boolean, default=False)

    # Security
    is_password_protected = Column(Boolean, default=False)
    password_hash = Column(String, nullable=True)

    # Pricing
    price = Column(Float, default=0.0)
    currency = Column(String, default="INR")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # Stats (denormalized for performance)
    total_enrollments = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    total_duration_minutes = Column(Integer, default=0)

    # Relationships
    # from app.models.category import course_tags

    instructor = relationship(
        "User", back_populates="courses_taught", foreign_keys=[instructor_id]
    )
    category_rel = relationship("Category", back_populates="courses")
    tags_rel = relationship("Tag", secondary="course_tags", back_populates="courses")

    modules = relationship(
        "Module",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Module.order_index",
    )
    enrollments = relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "CourseReview", back_populates="course", cascade="all, delete-orphan"
    )
    certificates = relationship(
        "Certificate", back_populates="course", cascade="all, delete-orphan"
    )
    # analytics = relationship("CourseAnalytics", back_populates="course", uselist=False, cascade="all, delete-orphan")  # TODO: CourseAnalytics model doesn't exist
    learning_groups = relationship("LearningGroup", back_populates="course")

    # Marketplace Relationships
    revenue_share = relationship(
        "RevenueShare",
        back_populates="course",
        uselist=False,
        cascade="all, delete-orphan",
    )
    marketplace_listing = relationship(
        "MarketplaceListing",
        back_populates="course",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def category(self):
        return self.category_rel

    def __repr__(self):
        return f"<Course {self.title}>"
