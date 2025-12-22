from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Table,
    DateTime,
    Numeric,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
from decimal import Decimal

# Association table for Many-to-Many relationship between Bundles and Courses
bundle_courses = Table(
    "course_bundle_items",
    Base.metadata,
    Column(
        "bundle_id",
        Integer,
        ForeignKey("course_bundles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "course_id",
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class CourseBundle(Base):
    __tablename__ = "course_bundles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    slug = Column(String(255), unique=True, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500))
    price = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    original_price = Column(Numeric(10, 2))  # Sum of individual prices
    discount_percentage = Column(Numeric(5, 2))
    currency = Column(String(3), default="USD")
    thumbnail_url = Column(String(500), nullable=True)
    banner_url = Column(String(500))
    is_published = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Bundle analytics
    total_enrollments = Column(Integer, default=0)
    total_revenue = Column(Numeric(10, 2), default=Decimal("0.00"))
    view_count = Column(Integer, default=0)

    # Validity period
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))

    # SEO
    meta_title = Column(String(255))
    meta_description = Column(Text)
    meta_keywords = Column(String(500))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    instructor = relationship("User", back_populates="bundles")
    courses = relationship("Course", secondary=bundle_courses, backref="bundles")
    enrollments = relationship(
        "BundleEnrollment", back_populates="bundle", cascade="all, delete-orphan"
    )


class BundleEnrollment(Base):
    __tablename__ = "bundle_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    bundle_id = Column(
        Integer, ForeignKey("course_bundles.id"), nullable=False, index=True
    )
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    price_paid = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    payment_id = Column(String(100), nullable=True)
    payment_status = Column(String(20), default="completed")

    # Coupon tracking
    coupon_code = Column(String(50))
    discount_applied = Column(Numeric(10, 2), default=Decimal("0.00"))

    # Progress tracking
    courses_completed = Column(Integer, default=0)
    completion_percentage = Column(Numeric(5, 2), default=Decimal("0.00"))
    completed_at = Column(DateTime(timezone=True))

    # Status
    status = Column(String(20), default="active")  # active, cancelled, refunded

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="bundle_enrollments")
    bundle = relationship("CourseBundle", back_populates="enrollments")
