"""
Bundle Service

Business logic for course bundle management, pricing, and enrollment.
"""

from sqlalchemy.orm import Session
from app.models.bundle import CourseBundle, BundleEnrollment
from app.models.course import Course
from app.services.revenue_service import RevenueShareService
from decimal import Decimal
from typing import Optional, List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BundleService:
    """Service for managing course bundles."""

    @staticmethod
    def create_bundle(
        db: Session,
        instructor_id: int,
        title: str,
        description: str,
        course_ids: List[int],
        discount_percentage: Decimal,
        slug: Optional[str] = None,
        **kwargs,
    ) -> CourseBundle:
        """
        Create a new course bundle.

        Args:
            db: Database session
            instructor_id: Creator instructor ID
            title: Bundle title
            description: Bundle description
            course_ids: List of course IDs to include
            discount_percentage: Discount off individual prices
            slug: URL slug
            **kwargs: Additional bundle attributes

        Returns:
            CourseBundle instance

        Raises:
            ValueError: If validation fails
        """
        # Validate courses
        if len(course_ids) < 2:
            raise ValueError("Bundle must contain at least 2 courses")

        courses = db.query(Course).filter(Course.id.in_(course_ids)).all()

        if len(courses) != len(course_ids):
            raise ValueError("One or more courses not found")

        # Verify instructor owns all courses
        for course in courses:
            if course.instructor_id != instructor_id:
                raise ValueError(f"Instructor does not own course: {course.title}")

        # Calculate pricing
        original_price = sum(Decimal(str(course.price)) for course in courses)
        discount_amount = original_price * (discount_percentage / Decimal("100"))
        final_price = original_price - discount_amount

        # Generate slug if not provided
        if not slug:
            import re

            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

        # Create bundle
        bundle = CourseBundle(
            title=title,
            slug=slug,
            description=description,
            instructor_id=instructor_id,
            price=final_price,
            original_price=original_price,
            discount_percentage=discount_percentage,
            **kwargs,
        )

        db.add(bundle)
        db.flush()  # Get the bundle ID

        # Add courses to bundle
        bundle.courses.extend(courses)

        db.commit()
        db.refresh(bundle)

        logger.info(
            f"Created bundle {bundle.id}: {title} with {len(courses)} courses at ${final_price}"
        )

        return bundle

    @staticmethod
    def update_bundle_pricing(db: Session, bundle_id: int) -> CourseBundle:
        """
        Recalculate bundle pricing based on current course prices.

        Args:
            db: Database session
            bundle_id: Bundle ID

        Returns:
            Updated bundle
        """
        bundle = db.query(CourseBundle).filter(CourseBundle.id == bundle_id).first()

        if not bundle:
            raise ValueError("Bundle not found")

        # Recalculate original price
        original_price = sum(Decimal(str(course.price)) for course in bundle.courses)

        # Apply discount
        discount_amount = original_price * (bundle.discount_percentage / Decimal("100"))
        final_price = original_price - discount_amount

        bundle.original_price = original_price
        bundle.price = final_price

        db.commit()
        db.refresh(bundle)

        logger.info(f"Updated bundle {bundle_id} pricing: ${final_price}")

        return bundle

    @staticmethod
    async def enroll_in_bundle(
        db: Session,
        user_id: int,
        bundle_id: int,
        payment_id: str,
        price_paid: Decimal,
        coupon_code: Optional[str] = None,
        discount_applied: Decimal = Decimal("0.00"),
    ) -> BundleEnrollment:
        """
        Enroll user in a bundle and all included courses.

        Args:
            db: Database session
            user_id: User ID
            bundle_id: Bundle ID
            payment_id: Payment transaction ID
            price_paid: Amount paid
            coupon_code: Applied coupon
            discount_applied: Discount amount

        Returns:
            BundleEnrollment instance
        """
        bundle = db.query(CourseBundle).filter(CourseBundle.id == bundle_id).first()

        if not bundle:
            raise ValueError("Bundle not found")

        # Check if already enrolled
        existing = (
            db.query(BundleEnrollment)
            .filter(
                BundleEnrollment.user_id == user_id,
                BundleEnrollment.bundle_id == bundle_id,
            )
            .first()
        )

        if existing:
            raise ValueError("Already enrolled in this bundle")

        # Create bundle enrollment
        enrollment = BundleEnrollment(
            user_id=user_id,
            bundle_id=bundle_id,
            price_paid=price_paid,
            payment_id=payment_id,
            coupon_code=coupon_code,
            discount_applied=discount_applied,
        )

        db.add(enrollment)

        # Enroll in all courses
        from app.models.enrollment import Enrollment

        for course in bundle.courses:
            # Check if already enrolled in course
            course_enrollment = (
                db.query(Enrollment)
                .filter(
                    Enrollment.user_id == user_id, Enrollment.course_id == course.id
                )
                .first()
            )

            if not course_enrollment:
                course_enrollment = Enrollment(
                    user_id=user_id,
                    course_id=course.id,
                    enrollment_type="bundle",
                    payment_id=payment_id,
                )
                db.add(course_enrollment)

        # Record revenue (split among course instructors)
        revenue_per_course = price_paid / len(bundle.courses)

        for course in bundle.courses:
            RevenueShareService.record_sale(
                db=db,
                course_id=course.id,
                instructor_id=course.instructor_id,
                student_id=user_id,
                amount=revenue_per_course,
                payment_id=payment_id,
                coupon_code=coupon_code,
                discount_amount=discount_applied / len(bundle.courses),
            )

        # Update bundle stats
        bundle.total_enrollments += 1
        bundle.total_revenue += price_paid

        db.commit()
        db.refresh(enrollment)

        logger.info(f"User {user_id} enrolled in bundle {bundle_id} for ${price_paid}")

        return enrollment

    @staticmethod
    def get_bundle_details(db: Session, bundle_id: int) -> Dict[str, any]:
        """
        Get detailed bundle information.

        Args:
            db: Database session
            bundle_id: Bundle ID

        Returns:
            Bundle details with included courses
        """
        bundle = db.query(CourseBundle).filter(CourseBundle.id == bundle_id).first()

        if not bundle:
            return None

        savings = bundle.original_price - bundle.price

        return {
            "id": bundle.id,
            "title": bundle.title,
            "slug": bundle.slug,
            "description": bundle.description,
            "price": bundle.price,
            "original_price": bundle.original_price,
            "discount_percentage": bundle.discount_percentage,
            "savings": savings,
            "course_count": len(bundle.courses),
            "courses": [
                {"id": course.id, "title": course.title, "price": course.price}
                for course in bundle.courses
            ],
            "total_enrollments": bundle.total_enrollments,
            "is_featured": bundle.is_featured,
            "is_published": bundle.is_published,
        }

    @staticmethod
    def get_user_bundles(db: Session, user_id: int) -> List[BundleEnrollment]:
        """
        Get all bundles user is enrolled in.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of bundle enrollments
        """
        return (
            db.query(BundleEnrollment)
            .filter(
                BundleEnrollment.user_id == user_id, BundleEnrollment.status == "active"
            )
            .all()
        )

    @staticmethod
    def update_bundle_progress(db: Session, enrollment_id: int):
        """
        Update bundle completion progress.

        Args:
            db: Database session
            enrollment_id: Bundle enrollment ID
        """
        enrollment = (
            db.query(BundleEnrollment)
            .filter(BundleEnrollment.id == enrollment_id)
            .first()
        )

        if not enrollment:
            return

        from app.models.enrollment import Enrollment

        # Count completed courses
        completed_count = 0
        total_courses = len(enrollment.bundle.courses)

        for course in enrollment.bundle.courses:
            course_enrollment = (
                db.query(Enrollment)
                .filter(
                    Enrollment.user_id == enrollment.user_id,
                    Enrollment.course_id == course.id,
                )
                .first()
            )

            if course_enrollment and course_enrollment.completion_percentage == 100:
                completed_count += 1

        enrollment.courses_completed = completed_count
        enrollment.completion_percentage = (
            Decimal(completed_count) / Decimal(total_courses)
        ) * Decimal("100")

        if completed_count == total_courses:
            enrollment.completed_at = datetime.utcnow()

        db.commit()

    @staticmethod
    def get_featured_bundles(db: Session, limit: int = 10) -> List[CourseBundle]:
        """
        Get featured bundles for marketplace homepage.

        Args:
            db: Database session
            limit: Max results

        Returns:
            List of featured bundles
        """
        return (
            db.query(CourseBundle)
            .filter(
                CourseBundle.is_published == True,
                CourseBundle.is_active == True,
                CourseBundle.is_featured == True,
            )
            .order_by(CourseBundle.total_enrollments.desc())
            .limit(limit)
            .all()
        )
