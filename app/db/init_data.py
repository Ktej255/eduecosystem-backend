import logging
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.task import Task, TaskType
from app.models.shadow_mode import ShadowModeSession
from app.models.submission import HandwritingSubmission

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    db = SessionLocal()

    try:
        # 1. Create Users
        logger.info("Creating users...")

        # Admin
        admin = db.query(User).filter(User.email == "ktej255@gmail.com").first()
        if not admin:
            admin = User(
                email="ktej255@gmail.com",
                full_name="Master Admin",
                hashed_password=get_password_hash("Tej@1106"),
                is_superuser=True,
                is_active=True,
                coins=1000,
                streak_days=10,
            )
            db.add(admin)

        # Teacher
        teacher = db.query(User).filter(User.email == "teacher@example.com").first()
        if not teacher:
            teacher = User(
                email="teacher@example.com",
                full_name="Professor Snape",
                hashed_password=get_password_hash("teacher123"),
                is_superuser=False,
                is_active=True,
                coins=500,
                streak_days=5,
            )
            db.add(teacher)

        # Student
        student = db.query(User).filter(User.email == "student@example.com").first()
        if not student:
            student = User(
                email="student@example.com",
                full_name="Harry Potter",
                hashed_password=get_password_hash("student123"),
                is_superuser=False,
                is_active=True,
                coins=150,
                streak_days=3,
            )
            db.add(student)

        db.commit()
        db.refresh(student)

        # 2. Create Tasks for Student
        logger.info("Creating tasks...")
        if not db.query(Task).filter(Task.user_id == student.id).first():
            tasks = [
                Task(
                    title="Complete Physics Assignment",
                    description="Chapter 5: Laws of Motion",
                    task_type=TaskType.OTHER,
                    duration_minutes=60,
                    user_id=student.id,
                    scheduled_date=datetime.utcnow() + timedelta(hours=2),
                    is_completed=False,
                ),
                Task(
                    title="Morning Meditation",
                    description="10 minutes mindfulness",
                    task_type=TaskType.MEDITATION,
                    duration_minutes=10,
                    user_id=student.id,
                    scheduled_date=datetime.utcnow() - timedelta(hours=4),
                    is_completed=True,
                ),
                Task(
                    title="Handwriting Analysis",
                    description="Upload sample for weekly check",
                    task_type=TaskType.GRAPHO,
                    duration_minutes=15,
                    user_id=student.id,
                    scheduled_date=datetime.utcnow() + timedelta(days=1),
                    is_completed=False,
                ),
            ]
            db.add_all(tasks)
            db.commit()

        # 3. Create Shadow Mode History
        logger.info("Creating shadow mode sessions...")
        if (
            not db.query(ShadowModeSession)
            .filter(ShadowModeSession.user_id == student.id)
            .first()
        ):
            # Create 3 completed days
            for i in range(1, 4):
                session = ShadowModeSession(
                    user_id=student.id,
                    day_number=i,
                    start_time=datetime.utcnow() - timedelta(days=4 - i, hours=2),
                    end_time=datetime.utcnow() - timedelta(days=4 - i),
                    duration_minutes=120,
                    goals_completed=3,
                    total_goals=3,
                    focus_score=8.5 + (i * 0.2),
                    notes=f"Day {i} completed successfully!",
                    is_active=False,
                )
                db.add(session)
            db.commit()

        # 4. Create Handwriting Submission
        logger.info("Creating handwriting submissions...")
        if (
            not db.query(HandwritingSubmission)
            .filter(HandwritingSubmission.user_id == student.id)
            .first()
        ):
            submission = HandwritingSubmission(
                user_id=student.id,
                image_url="uploads/sample_handwriting.jpg",
                quiz_data='{"morning_fatigue": "no", "high_t_bar": "yes"}',
                report_content='{"analysis": "Sample analysis content showing strong determination and high goals."}',
                report_level=1,
            )
            db.add(submission)
            db.commit()

        logger.info("Database initialized successfully!")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
