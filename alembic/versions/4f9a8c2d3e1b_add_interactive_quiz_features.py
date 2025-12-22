"""add_interactive_quiz_features

Revision ID: 4f9a8c2d3e1b
Revises: 3a771034232d
Create Date: 2025-11-25 08:45:00

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "4f9a8c2d3e1b"
down_revision = "3a771034232d"
branch_labels = None
depends_on = None


def upgrade():
    """Add interactive quiz features"""

    # 1. Add new columns to quizzes table
    with op.batch_alter_table("quizzes", schema=None) as batch_op:
        # Interactive Features
        batch_op.add_column(
            sa.Column(
                "instant_feedback", sa.Boolean(), nullable=True, server_default="1"
            )
        )
        batch_op.add_column(
            sa.Column(
                "show_score_immediately",
                sa.Boolean(),
                nullable=True,
                server_default="1",
            )
        )
        batch_op.add_column(
            sa.Column(
                "randomize_options", sa.Boolean(), nullable=True, server_default="0"
            )
        )
        batch_op.add_column(
            sa.Column(
                "allow_review_answers", sa.Boolean(), nullable=True, server_default="1"
            )
        )
        batch_op.add_column(
            sa.Column("show_hints", sa.Boolean(), nullable=True, server_default="0")
        )
        batch_op.add_column(
            sa.Column(
                "require_all_questions", sa.Boolean(), nullable=True, server_default="1"
            )
        )
        batch_op.add_column(
            sa.Column(
                "allow_backtrack", sa.Boolean(), nullable=True, server_default="1"
            )
        )

        # AI Grading Settings
        batch_op.add_column(
            sa.Column(
                "enable_ai_grading", sa.Boolean(), nullable=True, server_default="0"
            )
        )
        batch_op.add_column(
            sa.Column(
                "ai_grading_model", sa.String(), nullable=True, server_default="gemini"
            )
        )
        batch_op.add_column(
            sa.Column(
                "manual_review_threshold",
                sa.Float(),
                nullable=True,
                server_default="0.7",
            )
        )

    # 2. Add new columns to student_answers table
    with op.batch_alter_table("student_answers", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "time_spent_seconds", sa.Integer(), nullable=True, server_default="0"
            )
        )
        batch_op.add_column(
            sa.Column(
                "submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now()
            )
        )

    # 3. Create quiz_feedback table
    op.create_table(
        "quiz_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("feedback_for_correct", sa.Text(), nullable=True),
        sa.Column("feedback_for_incorrect", sa.Text(), nullable=True),
        sa.Column("hint_text", sa.Text(), nullable=True),
        sa.Column("explanation_url", sa.String(), nullable=True),
        sa.Column("media_url", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_quiz_feedback_question_id"),
        "quiz_feedback",
        ["question_id"],
        unique=False,
    )

    # 4. Create quiz_attempt_analytics table
    op.create_table(
        "quiz_attempt_analytics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column(
            "time_spent_seconds", sa.Integer(), nullable=True, server_default="0"
        ),
        sa.Column(
            "average_time_per_question", sa.Float(), nullable=True, server_default="0.0"
        ),
        sa.Column(
            "questions_answered", sa.Integer(), nullable=True, server_default="0"
        ),
        sa.Column("questions_correct", sa.Integer(), nullable=True, server_default="0"),
        sa.Column(
            "questions_incorrect", sa.Integer(), nullable=True, server_default="0"
        ),
        sa.Column("questions_skipped", sa.Integer(), nullable=True, server_default="0"),
        sa.Column(
            "questions_reviewed", sa.Integer(), nullable=True, server_default="0"
        ),
        sa.Column("difficulty_rating", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("times_backtracked", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("hints_used", sa.Integer(), nullable=True, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["quiz_attempts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id"),
    )
    op.create_index(
        op.f("ix_quiz_attempt_analytics_attempt_id"),
        "quiz_attempt_analytics",
        ["attempt_id"],
        unique=True,
    )

    # 5. Create assessment_rubrics table
    op.create_table(
        "assessment_rubrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("criteria_name", sa.String(), nullable=False),
        sa.Column("max_points", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("levels", sa.Text(), nullable=True),  # JSON string
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assessment_rubrics_question_id"),
        "assessment_rubrics",
        ["question_id"],
        unique=False,
    )

    # 6. Create ai_grading_results table
    op.create_table(
        "ai_grading_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_answer_id", sa.Integer(), nullable=False),
        sa.Column("ai_score", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("ai_feedback", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("rubric_scores", sa.Text(), nullable=True),  # JSON string
        sa.Column(
            "needs_manual_review", sa.Boolean(), nullable=True, server_default="0"
        ),
        sa.Column("instructor_override_score", sa.Float(), nullable=True),
        sa.Column("instructor_feedback", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_by_instructor", sa.Boolean(), nullable=True, server_default="0"
        ),
        sa.Column("model_used", sa.String(), nullable=True, server_default="gemini"),
        sa.Column("grading_time_seconds", sa.Float(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["student_answer_id"], ["student_answers.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_answer_id"),
    )
    op.create_index(
        op.f("ix_ai_grading_results_student_answer_id"),
        "ai_grading_results",
        ["student_answer_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_ai_grading_results_needs_manual_review"),
        "ai_grading_results",
        ["needs_manual_review"],
        unique=False,
    )


def downgrade():
    """Remove interactive quiz features"""

    # Drop tables in reverse order
    op.drop_index(
        op.f("ix_ai_grading_results_needs_manual_review"),
        table_name="ai_grading_results",
    )
    op.drop_index(
        op.f("ix_ai_grading_results_student_answer_id"), table_name="ai_grading_results"
    )
    op.drop_table("ai_grading_results")

    op.drop_index(
        op.f("ix_assessment_rubrics_question_id"), table_name="assessment_rubrics"
    )
    op.drop_table("assessment_rubrics")

    op.drop_index(
        op.f("ix_quiz_attempt_analytics_attempt_id"),
        table_name="quiz_attempt_analytics",
    )
    op.drop_table("quiz_attempt_analytics")

    op.drop_index(op.f("ix_quiz_feedback_question_id"), table_name="quiz_feedback")
    op.drop_table("quiz_feedback")

    # Remove columns from student_answers
    with op.batch_alter_table("student_answers", schema=None) as batch_op:
        batch_op.drop_column("submitted_at")
        batch_op.drop_column("time_spent_seconds")

    # Remove columns from quizzes
    with op.batch_alter_table("quizzes", schema=None) as batch_op:
        batch_op.drop_column("manual_review_threshold")
        batch_op.drop_column("ai_grading_model")
        batch_op.drop_column("enable_ai_grading")
        batch_op.drop_column("allow_backtrack")
        batch_op.drop_column("require_all_questions")
        batch_op.drop_column("show_hints")
        batch_op.drop_column("allow_review_answers")
        batch_op.drop_column("randomize_options")
        batch_op.drop_column("show_score_immediately")
        batch_op.drop_column("instant_feedback")
