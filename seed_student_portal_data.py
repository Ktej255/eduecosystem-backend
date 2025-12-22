"""
Seed Student Portal Data
Populates the database with sample courses, modules, lessons, and enrollments for testing.
"""
import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
import app.db.base  # Register models
from app.models.user import User
from app.models.course import Course
from app.models.module import Module
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment
from app.models.lesson_progress import LessonProgress
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MASTER_EMAIL = "ktej255@gmail.com"

def seed_data():
    db = SessionLocal()
    try:
        # Get Master User
        user = db.query(User).filter(User.email == MASTER_EMAIL).first()
        if not user:
            logger.error(f"User {MASTER_EMAIL} not found. Run setup_master_account.py first.")
            return

        logger.info(f"Seeding data for user: {user.email}")

        # 1. Create Python Course
        python_course = db.query(Course).filter(Course.title == "Python for Beginners").first()
        if not python_course:
            logger.info("Creating 'Python for Beginners' course...")
            python_course = Course(
                title="Python for Beginners",
                slug="python-for-beginners",
                description="Master Python programming from scratch with hands-on projects. Learn variables, loops, functions, and more.",
                thumbnail_url="https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&q=80",
                instructor_id=user.id,
                price=0,
                is_published=True
            )
            db.add(python_course)
            db.commit()
            db.refresh(python_course)

            # Modules
            m1 = Module(course_id=python_course.id, title="Introduction to Python", order_index=1)
            m2 = Module(course_id=python_course.id, title="Variables and Data Types", order_index=2)
            db.add_all([m1, m2])
            db.commit()
            db.refresh(m1)
            db.refresh(m2)

            # Lessons M1
            l1 = Lesson(module_id=m1.id, title="Welcome to the Course", content="Welcome video...", duration="5:00", order_index=1, type="video")
            l2 = Lesson(module_id=m1.id, title="Setting up Python", content="Setup guide...", duration="10:00", order_index=2, type="video")
            l3 = Lesson(module_id=m1.id, title="Your First Program", content="Hello World...", duration="15:00", order_index=3, type="video")
            
            # Lessons M2
            l4 = Lesson(module_id=m2.id, title="Variables Explained", content="Variables...", duration="12:00", order_index=1, type="video")
            l5 = Lesson(module_id=m2.id, title="Numbers and Strings", content="Data types...", duration="18:00", order_index=2, type="video")
            
            db.add_all([l1, l2, l3, l4, l5])
            db.commit()

        # 2. Create Web Dev Course
        web_course = db.query(Course).filter(Course.title == "Web Development Fundamentals").first()
        if not web_course:
            logger.info("Creating 'Web Development Fundamentals' course...")
            web_course = Course(
                title="Web Development Fundamentals",
                slug="web-development-fundamentals",
                description="Learn HTML, CSS, and JavaScript to build modern websites.",
                thumbnail_url="https://images.unsplash.com/photo-1547658719-da2b51169166?w=800&q=80",
                instructor_id=user.id,
                price=0,
                is_published=True
            )
            db.add(web_course)
            db.commit()
            db.refresh(web_course)
            
            m1 = Module(course_id=web_course.id, title="HTML Basics", order_index=1)
            db.add(m1)
            db.commit()
            db.refresh(m1)
            
            l1 = Lesson(module_id=m1.id, title="HTML Structure", content="Tags and elements...", duration="8:00", order_index=1, type="video")
            db.add(l1)
            db.commit()

        # 3. Enroll User
        for course in [python_course, web_course]:
            enrollment = db.query(Enrollment).filter(
                Enrollment.user_id == user.id,
                Enrollment.course_id == course.id
            ).first()
            
            if not enrollment:
                logger.info(f"Enrolling user in {course.title}...")
                enrollment = Enrollment(
                    user_id=user.id,
                    course_id=course.id,
                    status="active"
                )
                db.add(enrollment)
        
        db.commit()

        # 4. Add some progress for Python course
        # Complete first 2 lessons
        lessons = db.query(Lesson).join(Module).filter(Module.course_id == python_course.id).order_by(Module.order_index, Lesson.order_index).all()
        
        for i, lesson in enumerate(lessons[:2]):
            prog = db.query(LessonProgress).filter(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id == lesson.id
            ).first()
            
            if not prog:
                logger.info(f"Marking lesson '{lesson.title}' as complete...")
                prog = LessonProgress(
                    user_id=user.id,
                    lesson_id=lesson.id,
                    course_id=python_course.id,
                    is_completed=True,
                    completed_at=datetime.utcnow()
                )
                db.add(prog)
        
        # Update enrollment progress
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user.id,
            Enrollment.course_id == python_course.id
        ).first()
        # enrollment.progress = 35
        db.commit()

        logger.info("✅ Data seeding complete!")

    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
