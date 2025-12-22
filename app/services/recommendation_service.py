"""Recommendation service for personalized course suggestions"""

from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.models.course import Course
from app.models.enrollment import Enrollment


class RecommendationService:
    """AI-powered recommendation engine using hybrid filtering"""

    def __init__(self, db: Session):
        self.db = db

    def get_personalized_recommendations(
        self, user_id: int, limit: int = 10, exclude_enrolled: bool = True
    ) -> List[Dict]:
        """
        Get personalized course recommendations using hybrid approach
        Combines collaborative filtering, content-based filtering, and popularity
        """
        # Get user's enrolled courses
        user_enrollments = (
            self.db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
        )

        enrolled_course_ids = {e.course_id for e in user_enrollments}

        # Get all available courses
        all_courses = self.db.query(Course).filter(Course.is_published == True).all()

        # Calculate scores for each course
        recommendations = []
        for course in all_courses:
            if exclude_enrolled and course.id in enrolled_course_ids:
                continue

            # Collaborative filtering score
            cf_score = self._collaborative_filtering_score(
                user_id, course.id, enrolled_course_ids
            )

            # Content-based filtering score
            cb_score = self._content_based_score(user_id, course, user_enrollments)

            # Popularity score
            popularity_score = self._popularity_score(course)

            # Hybrid score (weighted combination)
            final_score = 0.4 * cf_score + 0.4 * cb_score + 0.2 * popularity_score

            # Determine recommendation reason
            reason = self._get_recommendation_reason(
                cf_score, cb_score, popularity_score, course, user_enrollments
            )

            recommendations.append(
                {
                    "course_id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "category": course.category.name if course.category else "Uncategorized",
                    "level": course.level,
                    "rating": course.average_rating or 0,
                    "total_enrollments": course.total_enrollments or 0,
                    "price": course.price,
                    "instructor_name": course.instructor.full_name
                    if course.instructor
                    else "Unknown",
                    "score": round(final_score, 2),
                    "reason": reason,
                }
            )

        # Sort by score and return top N
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]

    def _collaborative_filtering_score(
        self, user_id: int, course_id: int, user_enrolled_courses: set
    ) -> float:
        """
        Calculate collaborative filtering score
        Find users with similar enrollment patterns
        """
        if not user_enrolled_courses:
            return 0.0

        # Find users who enrolled in same courses
        similar_users = (
            self.db.query(Enrollment.user_id)
            .filter(
                Enrollment.course_id.in_(user_enrolled_courses),
                Enrollment.user_id != user_id,
            )
            .group_by(Enrollment.user_id)
            .having(
                func.count(Enrollment.course_id) >= min(2, len(user_enrolled_courses))
            )
            .all()
        )

        similar_user_ids = [u[0] for u in similar_users]

        if not similar_user_ids:
            return 0.0

        # Check if similar users enrolled in target course
        similar_enrollments = (
            self.db.query(func.count(Enrollment.id))
            .filter(
                Enrollment.user_id.in_(similar_user_ids),
                Enrollment.course_id == course_id,
            )
            .scalar()
        )

        # Normalize score
        score = similar_enrollments / len(similar_user_ids) if similar_user_ids else 0
        return min(score, 1.0)

    def _content_based_score(
        self, user_id: int, course: Course, user_enrollments: List[Enrollment]
    ) -> float:
        """
        Calculate content-based filtering score
        Match course features with user preferences
        """
        if not user_enrollments:
            return 0.5  # Neutral score for new users

        # Extract user preferences from enrolled courses
        enrolled_courses = [e.course for e in user_enrollments]

        # Category preference
        user_category_ids = [c.category_id for c in enrolled_courses if c.category_id]
        category_match = 1.0 if course.category_id in user_category_ids else 0.0

        # Level preference
        user_levels = [c.level for c in enrolled_courses if c.level]
        level_match = 1.0 if course.level in user_levels else 0.5

        # Instructor preference (if user completed courses from this instructor)
        instructor_match = 0.0
        if course.instructor_id:
            completed_from_instructor = any(
                e.course.instructor_id == course.instructor_id
                and e.progress_percentage >= 80
                for e in user_enrollments
            )
            instructor_match = 1.0 if completed_from_instructor else 0.0

        # Weighted combination
        score = 0.5 * category_match + 0.3 * level_match + 0.2 * instructor_match

        return score

    def _popularity_score(self, course: Course) -> float:
        """Calculate popularity score based on enrollments and ratings"""
        # Normalize enrollment count (assuming max 10000 enrollments)
        enrollment_score = min((course.total_enrollments or 0) / 10000, 1.0)

        # Normalize rating (0-5 scale to 0-1)
        rating_score = (course.average_rating or 0) / 5.0

        # Combine both
        return 0.6 * enrollment_score + 0.4 * rating_score

    def _get_recommendation_reason(
        self,
        cf_score: float,
        cb_score: float,
        pop_score: float,
        course: Course,
        user_enrollments: List[Enrollment],
    ) -> str:
        """Generate human-readable recommendation reason"""
        if cf_score > 0.5:
            return "Students like you also enrolled in this course"
        elif cb_score > 0.7 and user_enrollments:
            similar_course = max(
                user_enrollments,
                key=lambda e: 1.0 if e.course.category_id == course.category_id else 0.0,
            ).course
            category_name = similar_course.category.name if similar_course.category else "Uncategorized"
            return f"Based on your interest in {category_name}"
        elif pop_score > 0.6:
            return "Trending course with great reviews"
        elif course.level:
            return f"Recommended {course.level} level course for you"
        else:
            return "Recommended for you"

    def get_similar_courses(self, course_id: int, limit: int = 5) -> List[Dict]:
        """Get courses similar to the given course"""
        target_course = self.db.query(Course).filter(Course.id == course_id).first()
        if not target_course:
            return []

        # Find courses with similar attributes
        similar_courses = (
            self.db.query(Course)
            .filter(
                Course.id != course_id,
                Course.is_published == True,
                Course.category_id == target_course.category_id,
            )
            .all()
        )

        # Calculate similarity scores
        similarities = []
        for course in similar_courses:
            score = self._calculate_course_similarity(target_course, course)
            similarities.append(
                {
                    "course_id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "category": course.category.name if course.category else "Uncategorized",
                    "level": course.level,
                    "rating": course.average_rating or 0,
                    "similarity_score": round(score, 2),
                    "price": course.price,
                }
            )

        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similarities[:limit]

    def _calculate_course_similarity(self, course1: Course, course2: Course) -> float:
        """Calculate similarity between two courses"""
        score = 0.0

        # Category match (40%)
        if course1.category_id == course2.category_id:
            score += 0.4

        # Level match (30%)
        if course1.level == course2.level:
            score += 0.3

        # Instructor match (20%)
        if course1.instructor_id == course2.instructor_id:
            score += 0.2

        # Price similarity (10%)
        if course1.price and course2.price:
            price_diff = abs(course1.price - course2.price)
            max_price = max(course1.price, course2.price)
            price_similarity = 1.0 - (price_diff / max_price) if max_price > 0 else 1.0
            score += 0.1 * price_similarity

        return score

    def get_trending_courses(self, limit: int = 10, days: int = 7) -> List[Dict]:
        """Get trending courses based on recent enrollments"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Count recent enrollments per course
        trending = (
            self.db.query(Course, func.count(Enrollment.id).label("recent_enrollments"))
            .join(Enrollment, Course.id == Enrollment.course_id)
            .filter(Course.is_published == True, Enrollment.enrolled_at >= cutoff_date)
            .group_by(Course.id)
            .order_by(desc("recent_enrollments"))
            .limit(limit)
            .all()
        )

        return [
            {
                "course_id": course.id,
                "title": course.title,
                "description": course.description,
                "category": course.category.name if course.category else "Uncategorized",
                "level": course.level,
                "rating": course.average_rating or 0,
                "total_enrollments": course.total_enrollments or 0,
                "recent_enrollments": recent_count,
                "price": course.price,
                "instructor_name": course.instructor.full_name
                if course.instructor
                else "Unknown",
            }
            for course, recent_count in trending
        ]


# Singleton instance
recommendation_service = RecommendationService
