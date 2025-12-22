"""Add LMS models

Revision ID: add_lms_models
Revises:
Create Date: 2025-11-22

"""

revision = "add_lms_models"
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Create courses table
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("long_description", sa.Text(), nullable=True),
        sa.Column("instructor_id", sa.Integer(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "programming",
                "data_science",
                "design",
                "business",
                "marketing",
                "personal_development",
                "health",
                "language",
                "other",
                name="coursecategory",
            ),
            nullable=True,
        ),
        sa.Column(
            "level",
            sa.Enum("beginner", "intermediate", "advanced", name="courselevel"),
            nullable=True,
        ),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("thumbnail_url", sa.String(), nullable=True),
        sa.Column("preview_video_url", sa.String(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("page_layout", sa.JSON(), nullable=True),
        sa.Column("prerequisites", sa.JSON(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("total_enrollments", sa.Integer(), nullable=True),
        sa.Column("average_rating", sa.Float(), nullable=True),
        sa.Column("total_reviews", sa.Integer(), nullable=True),
        sa.Column("total_duration_minutes", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["instructor_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_courses_id"), "courses", ["id"], unique=False)
    op.create_index(op.f("ix_courses_title"), "courses", ["title"], unique=False)
    op.create_index(
        op.f("ix_courses_instructor_id"), "courses", ["instructor_id"], unique=False
    )
    op.create_index(op.f("ix_courses_category"), "courses", ["category"], unique=False)
    op.create_index(op.f("ix_courses_level"), "courses", ["level"], unique=False)
    op.create_index(
        op.f("ix_courses_is_published"), "courses", ["is_published"], unique=False
    )

    # Create modules table
    op.create_table(
        "modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=True),
        sa.Column("quiz_id", sa.Integer(), nullable=True),
        sa.Column("assignment_prompts", sa.JSON(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["quiz_id"],
            ["quizzes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_modules_id"), "modules", ["id"], unique=False)
    op.create_index(
        op.f("ix_modules_course_id"), "modules", ["course_id"], unique=False
    )
    op.create_index(
        op.f("ix_modules_order_index"), "modules", ["order_index"], unique=False
    )

    # Create lessons table
    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "type",
            sa.Enum(
                "video",
                "text",
                "quiz",
                "assignment",
                "interactive",
                "live_class",
                "download",
                name="lessontype",
            ),
            nullable=True,
        ),
        sa.Column("content", sa.JSON(), nullable=True),
        sa.Column("video_url", sa.String(), nullable=True),
        sa.Column("video_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=True),
        sa.Column("is_preview", sa.Boolean(), nullable=True),
        sa.Column("available_after_days", sa.Integer(), nullable=True),
        sa.Column("prerequisite_lesson_ids", sa.JSON(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lessons_id"), "lessons", ["id"], unique=False)
    op.create_index(
        op.f("ix_lessons_module_id"), "lessons", ["module_id"], unique=False
    )
    op.create_index(op.f("ix_lessons_type"), "lessons", ["type"], unique=False)
    op.create_index(
        op.f("ix_lessons_order_index"), "lessons", ["order_index"], unique=False
    )

    # Create enrollments table
    op.create_table(
        "enrollments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "active", "completed", "dropped", "expired", name="enrollmentstatus"
            ),
            nullable=True,
        ),
        sa.Column("progress_percentage", sa.Float(), nullable=True),
        sa.Column("last_accessed_lesson_id", sa.Integer(), nullable=True),
        sa.Column("enrolled_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("price_paid", sa.Float(), nullable=True),
        sa.Column("certificate_issued", sa.Boolean(), nullable=True),
        sa.Column("certificate_issued_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["last_accessed_lesson_id"],
            ["lessons.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_enrollments_id"), "enrollments", ["id"], unique=False)
    op.create_index(
        op.f("ix_enrollments_user_id"), "enrollments", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_enrollments_course_id"), "enrollments", ["course_id"], unique=False
    )
    op.create_index(
        op.f("ix_enrollments_status"), "enrollments", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_enrollments_enrolled_at"), "enrollments", ["enrolled_at"], unique=False
    )

    # Create lesson_progress table
    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("not_started", "in_progress", "completed", name="progressstatus"),
            nullable=True,
        ),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True),
        sa.Column("video_progress_seconds", sa.Integer(), nullable=True),
        sa.Column("video_completed_percentage", sa.Float(), nullable=True),
        sa.Column("result_data", sa.JSON(), nullable=True),
        sa.Column("first_accessed_at", sa.DateTime(), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_lesson_progress_id"), "lesson_progress", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_lesson_progress_user_id"), "lesson_progress", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_lesson_progress_lesson_id"),
        "lesson_progress",
        ["lesson_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lesson_progress_status"), "lesson_progress", ["status"], unique=False
    )

    # Create course_reviews table
    op.create_table(
        "course_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_approved", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_course_reviews_id"), "course_reviews", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_course_reviews_course_id"),
        "course_reviews",
        ["course_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_course_reviews_user_id"), "course_reviews", ["user_id"], unique=False
    )


def downgrade():
    op.drop_table("course_reviews")
    op.drop_table("lesson_progress")
    op.drop_table("enrollments")
    op.drop_table("lessons")
    op.drop_table("modules")
    op.drop_table("courses")

    # Drop enums
    sa.Enum(name="coursecategory").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="courselevel").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="lessontype").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="progressstatus").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="enrollmentstatus").drop(op.get_bind(), checkfirst=False)
