"""
Seed data for LMS - creates sample courses, modules, and lessons
Run this after running migrations
"""

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.course import Course, CourseCategory, CourseLevel
from app.models.module import Module
from app.models.lesson import Lesson, LessonType
from app.models.user import User
from app.core.security import get_password_hash


def create_sample_instructor(db: Session):
    """Create a sample instructor user"""
    instructor = (
        db.query(User).filter(User.email == "instructor@eduecosystem.com").first()
    )
    if not instructor:
        instructor = User(
            email="instructor@eduecosystem.com",
            hashed_password=get_password_hash("instructor123"),
            full_name="Dr. Sarah Chen",
            is_active=True,
            role="user",
        )
        db.add(instructor)
        db.commit()
        db.refresh(instructor)
        print(f"✅ Created instructor: {instructor.email}")
    return instructor


def seed_lms_data():
    """Create sample LMS courses"""
    db = SessionLocal()

    try:
        # Create instructor
        instructor = create_sample_instructor(db)

        # Course 1: Python for Beginners
        python_course = Course(
            title="Python Programming for Beginners",
            description="Learn Python from scratch with hands-on projects and real-world examples",
            long_description="""
            Master Python programming in this comprehensive beginner course. You'll start with the basics 
            and progress to building real applications. Perfect for absolute beginners with no prior 
            programming experience.
            
            What You'll Learn:
            - Python syntax and fundamentals
            - Data structures and algorithms
            - Object-oriented programming
            - File handling and modules
            - Building practical projects
            """,
            instructor_id=instructor.id,
            category=CourseCategory.PROGRAMMING,
            level=CourseLevel.BEGINNER,
            tags=["python", "programming", "coding", "beginner-friendly"],
            thumbnail_url="https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800",
            price=49.99,
            currency="USD",
            is_published=True,
            is_featured=True,
            total_duration_minutes=300,
        )
        db.add(python_course)
        db.commit()
        db.refresh(python_course)
        print(f"✅ Created course: {python_course.title}")

        # Module 1: Getting Started
        module1 = Module(
            course_id=python_course.id,
            title="Getting Started with Python",
            description="Introduction to Python and setting up your development environment",
            order_index=0,
            duration_minutes=60,
        )
        db.add(module1)
        db.commit()
        db.refresh(module1)

        # Lessons for Module 1
        lessons_m1 = [
            Lesson(
                module_id=module1.id,
                title="Welcome to Python Programming",
                description="Course overview and what you'll learn",
                type=LessonType.VIDEO,
                content={
                    "markdown": "Welcome to the course! Get ready to learn Python programming."
                },
                video_url="https://example.com/videos/welcome.mp4",
                order_index=0,
                duration_minutes=10,
                is_preview=True,
            ),
            Lesson(
                module_id=module1.id,
                title="Installing Python and VS Code",
                description="Set up your development environment",
                type=LessonType.TEXT,
                content={
                    "markdown": """
                # Installing Python
                
                1. Download Python from python.org
                2. Install VS Code from code.visualstudio.com
                3. Install Python extension in VS Code
                4. Verify installation by running `python --version`
                """
                },
                order_index=1,
                duration_minutes=15,
            ),
            Lesson(
                module_id=module1.id,
                title="Your First Python Program",
                description="Write and run your first Python script",
                type=LessonType.VIDEO,
                content={"markdown": "Learn to write Hello World in Python"},
                video_url="https://example.com/videos/first-program.mp4",
                order_index=2,
                duration_minutes=20,
            ),
            Lesson(
                module_id=module1.id,
                title="Quiz: Python Basics",
                description="Test your knowledge of Python fundamentals",
                type=LessonType.QUIZ,
                content={"quiz_id": None},  # Will be linked to actual quiz later
                order_index=3,
                duration_minutes=15,
            ),
        ]

        for lesson in lessons_m1:
            db.add(lesson)
        db.commit()
        print(f"✅ Created {len(lessons_m1)} lessons for Module 1")

        # Module 2: Python Fundamentals
        module2 = Module(
            course_id=python_course.id,
            title="Python Fundamentals",
            description="Learn variables, data types, and control structures",
            order_index=1,
            duration_minutes=90,
        )
        db.add(module2)
        db.commit()
        db.refresh(module2)

        # Lessons for Module 2
        lessons_m2 = [
            Lesson(
                module_id=module2.id,
                title="Variables and Data Types",
                description="Understanding Python variables and basic data types",
                type=LessonType.VIDEO,
                content={
                    "markdown": "Learn about int, float, string, and boolean types"
                },
                video_url="https://example.com/videos/variables.mp4",
                order_index=0,
                duration_minutes=25,
            ),
            Lesson(
                module_id=module2.id,
                title="Lists and Dictionaries",
                description="Working with Python collections",
                type=LessonType.VIDEO,
                content={"markdown": "Master lists, tuples, and dictionaries"},
                video_url="https://example.com/videos/collections.mp4",
                order_index=1,
                duration_minutes=30,
            ),
            Lesson(
                module_id=module2.id,
                title="Control Flow: If-Else Statements",
                description="Making decisions in your code",
                type=LessonType.TEXT,
                content={
                    "markdown": """
                # Control Flow in Python
                
                ## If Statements
                ```python
                age = 18
                if age >= 18:
                    print("You can vote!")
                else:
                    print("Too young to vote")
                ```
                """
                },
                order_index=2,
                duration_minutes=20,
            ),
            Lesson(
                module_id=module2.id,
                title="Practice Assignment",
                description="Build a simple calculator",
                type=LessonType.ASSIGNMENT,
                content={
                    "instructions": "Create a calculator that performs basic arithmetic operations"
                },
                order_index=3,
                duration_minutes=15,
            ),
        ]

        for lesson in lessons_m2:
            db.add(lesson)
        db.commit()
        print(f"✅ Created {len(lessons_m2)} lessons for Module 2")

        # Course 2: Data Science with Python
        ds_course = Course(
            title="Data Science Fundamentals",
            description="Learn data analysis, visualization, and machine learning with Python",
            long_description="""
            Dive into the world of data science! This course teaches you how to analyze data, 
            create stunning visualizations, and build machine learning models using Python.
            
            Prerequisites: Basic Python knowledge
            """,
            instructor_id=instructor.id,
            category=CourseCategory.DATA_SCIENCE,
            level=CourseLevel.INTERMEDIATE,
            tags=["data-science", "python", "machine-learning", "pandas", "numpy"],
            thumbnail_url="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
            price=79.99,
            currency="USD",
            is_published=True,
            total_duration_minutes=450,
        )
        db.add(ds_course)
        db.commit()
        print(f"✅ Created course: {ds_course.title}")

        # Module for DS course
        ds_module = Module(
            course_id=ds_course.id,
            title="Introduction to Pandas",
            description="Data manipulation and analysis with Pandas",
            order_index=0,
            duration_minutes=120,
        )
        db.add(ds_module)
        db.commit()

        # Sample lessons for DS course
        ds_lessons = [
            Lesson(
                module_id=ds_module.id,
                title="What is Data Science?",
                description="Introduction to the field of data science",
                type=LessonType.VIDEO,
                video_url="https://example.com/videos/ds-intro.mp4",
                order_index=0,
                duration_minutes=20,
                is_preview=True,
            ),
            Lesson(
                module_id=ds_module.id,
                title="Pandas DataFrames Basics",
                description="Learn to work with DataFrames",
                type=LessonType.TEXT,
                content={
                    "markdown": "# Working with Pandas\n\nDataFrames are the core data structure..."
                },
                order_index=1,
                duration_minutes=40,
            ),
        ]

        for lesson in ds_lessons:
            db.add(lesson)
        db.commit()
        print(f"✅ Created {len(ds_lessons)} lessons for Data Science course")

        print("\n🎉 LMS seed data created successfully!")
        print(f"   - {db.query(Course).count()} courses")
        print(f"   - {db.query(Module).count()} modules")
        print(f"   - {db.query(Lesson).count()} lessons")

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_lms_data()
