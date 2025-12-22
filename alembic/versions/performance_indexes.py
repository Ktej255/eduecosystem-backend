"""Add performance indexes for LMS tables

Revision ID: performance_indexes
Revises: d5635fa1af10
Create Date: 2025-11-22
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "performance_indexes"
# Updated down_revision to follow linear chain
down_revision = "add_blockchain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes"""
    # Course indexes (already exist)
    # op.create_index('ix_courses_created_at', 'courses', ['created_at'])  # Already exists
    # op.create_index('ix_courses_published_at', 'courses', ['published_at'])  # Already exists

    # Enrollment indexes for common queries
    op.create_index(
        "ix_enrollments_user_created", "enrollments", ["user_id", "enrolled_at"]
    )
    op.create_index(
        "ix_enrollments_course_created", "enrollments", ["course_id", "enrolled_at"]
    )

    # Lesson Progress indexes
    op.create_index(
        "ix_lesson_progress_user_lesson", "lesson_progress", ["user_id", "lesson_id"]
    )
    op.create_index("ix_lesson_progress_completed", "lesson_progress", ["completed_at"])

    # Course Payment indexes
    op.create_index(
        "ix_course_payments_user_created", "course_payments", ["user_id", "created_at"]
    )
    op.create_index("ix_course_payments_status", "course_payments", ["payment_status"])

    # Quiz Attempt indexes
    op.create_index(
        "ix_quiz_attempts_user_quiz", "quiz_attempts", ["user_id", "quiz_id"]
    )
    op.create_index("ix_quiz_attempts_submitted", "quiz_attempts", ["submitted_at"])

    # Assignment Submission indexes
    op.create_index(
        "ix_assignment_submissions_user_assignment",
        "assignment_submissions",
        ["user_id", "assignment_id"],
    )
    op.create_index(
        "ix_assignment_submissions_status", "assignment_submissions", ["status"]
    )


def downgrade() -> None:
    """Remove performance indexes"""
    # Course indexes
    op.drop_index("ix_courses_created_at", table_name="courses")
    op.drop_index("ix_courses_published_at", table_name="courses")

    # Enrollment indexes
    op.drop_index("ix_enrollments_user_created", table_name="enrollments")
    op.drop_index("ix_enrollments_course_created", table_name="enrollments")

    # Lesson Progress indexes
    op.drop_index("ix_lesson_progress_user_lesson", table_name="lesson_progress")
    op.drop_index("ix_lesson_progress_completed", table_name="lesson_progress")

    # Course Payment indexes
    op.drop_index("ix_course_payments_user_created", table_name="course_payments")
    op.drop_index("ix_course_payments_status", table_name="course_payments")

    # Quiz Attempt indexes
    op.drop_index("ix_quiz_attempts_user_quiz", table_name="quiz_attempts")
    op.drop_index("ix_quiz_attempts_submitted", table_name="quiz_attempts")

    # Assignment Submission indexes
    op.drop_index(
        "ix_assignment_submissions_user_assignment", table_name="assignment_submissions"
    )
    op.drop_index(
        "ix_assignment_submissions_status", table_name="assignment_submissions"
    )
