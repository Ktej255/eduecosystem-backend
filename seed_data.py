"""
Sample Data Seeder for Eduecosystem LMS
Creates sample courses, modules, and lessons for testing
Run from backend directory: python seed_data.py
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models import Course, Module, Lesson, User
from sqlalchemy.orm import Session
import re


def slugify(text):
    text = text.lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def create_sample_instructor(db: Session):
    """Create a sample instructor user"""
    instructor = db.query(User).filter(User.email == "instructor@test.com").first()

    if not instructor:
        instructor = User(
            email="instructor@test.com",
            full_name="Dr. Sarah Johnson",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OQGwHfN7L3ve",  # "password123"
            is_superuser=False,
            role="instructor",
            coins=100,
            streak_days=7,
        )
        db.add(instructor)
        db.commit()
        db.refresh(instructor)
        print(f"✅ Created instructor: {instructor.email}")
    else:
        print(f"ℹ️  Instructor already exists: {instructor.email}")

    return instructor


def create_sample_courses(db: Session, instructor_id: int):
    """Create sample courses with modules and lessons"""

    courses_data = [
        {
            "title": "Introduction to Python Programming",
            "description": "Learn Python from scratch with hands-on projects. Perfect for beginners who want to start coding!",
            "level": "beginner",
            "price": 0.0,
            "is_published": True,
            "modules": [
                {
                    "title": "Getting Started with Python",
                    "order_index": 0,
                    "lessons": [
                        {
                            "title": "What is Python?",
                            "content": "Introduction to Python programming language",
                            "duration_minutes": 15,
                            "order_index": 0,
                        },
                        {
                            "title": "Installing Python",
                            "content": "How to install Python on your computer",
                            "duration_minutes": 10,
                            "order_index": 1,
                        },
                        {
                            "title": "Your First Program",
                            "content": "Writing and running your first Python program",
                            "duration_minutes": 20,
                            "order_index": 2,
                        },
                    ],
                },
                {
                    "title": "Python Basics",
                    "order_index": 1,
                    "lessons": [
                        {
                            "title": "Variables and Data Types",
                            "content": "Understanding variables, strings, numbers, and booleans",
                            "duration_minutes": 25,
                            "order_index": 0,
                        },
                        {
                            "title": "Operators",
                            "content": "Arithmetic, comparison, and logical operators",
                            "duration_minutes": 20,
                            "order_index": 1,
                        },
                    ],
                },
            ],
        },
        {
            "title": "Web Development with React",
            "description": "Build modern web applications with React and Next.js. Learn component-based architecture and state management.",
            "level": "intermediate",
            "price": 49.99,
            "is_published": True,
            "modules": [
                {
                    "title": "React Fundamentals",
                    "order_index": 0,
                    "lessons": [
                        {
                            "title": "What is React?",
                            "content": "Introduction to React library",
                            "duration_minutes": 15,
                            "order_index": 0,
                        },
                        {
                            "title": "Components and Props",
                            "content": "Creating reusable components",
                            "duration_minutes": 30,
                            "order_index": 1,
                        },
                        {
                            "title": "State and Hooks",
                            "content": "Managing component state with hooks",
                            "duration_minutes": 35,
                            "order_index": 2,
                        },
                    ],
                }
            ],
        },
        {
            "title": "Data Science with Python",
            "description": "Master data analysis, visualization, and machine learning using Python, NumPy, Pandas, and Scikit-learn.",
            "level": "intermediate",
            "price": 79.99,
            "is_published": True,
            "modules": [
                {
                    "title": "Data Analysis Basics",
                    "order_index": 0,
                    "lessons": [
                        {
                            "title": "Introduction to NumPy",
                            "content": "Working with arrays and matrices",
                            "duration_minutes": 25,
                            "order_index": 0,
                        },
                        {
                            "title": "Pandas DataFrames",
                            "content": "Data manipulation with Pandas",
                            "duration_minutes": 30,
                            "order_index": 1,
                        },
                    ],
                }
            ],
        },
        {
            "title": "UI/UX Design Principles",
            "description": "Learn to create beautiful, user-friendly interfaces. Covers design theory, prototyping, and user research.",
            "level": "beginner",
            "price": 0.0,
            "is_published": True,
            "modules": [
                {
                    "title": "Design Fundamentals",
                    "order_index": 0,
                    "lessons": [
                        {
                            "title": "Design Thinking",
                            "content": "User-centered design approach",
                            "duration_minutes": 20,
                            "order_index": 0,
                        },
                        {
                            "title": "Color Theory",
                            "content": "Using colors effectively in design",
                            "duration_minutes": 25,
                            "order_index": 1,
                        },
                    ],
                }
            ],
        },
        {
            "title": "Digital Marketing Mastery",
            "description": "Comprehensive guide to digital marketing covering SEO, social media, email marketing, and analytics.",
            "level": "beginner",
            "price": 39.99,
            "is_published": True,
            "modules": [
                {
                    "title": "Marketing Foundations",
                    "order_index": 0,
                    "lessons": [
                        {
                            "title": "Digital Marketing Overview",
                            "content": "Introduction to digital marketing channels",
                            "duration_minutes": 20,
                            "order_index": 0,
                        },
                        {
                            "title": "SEO Basics",
                            "content": "Search engine optimization fundamentals",
                            "duration_minutes": 30,
                            "order_index": 1,
                        },
                    ],
                }
            ],
        },
    ]

    created_courses = []

    for course_data in courses_data:
        # Check if course already exists
        existing_course = (
            db.query(Course).filter(Course.title == course_data["title"]).first()
        )

        if existing_course:
            print(f"ℹ️  Course already exists: {course_data['title']}")
            created_courses.append(existing_course)
            continue

        # Create course
        modules_data = course_data.pop("modules")
        course = Course(
            instructor_id=instructor_id,
            slug=slugify(course_data["title"]),
            **course_data,
        )
        db.add(course)
        db.flush()  # Get course.id

        # Create modules and lessons
        for module_data in modules_data:
            lessons_data = module_data.pop("lessons")
            module = Module(course_id=course.id, **module_data)
            db.add(module)
            db.flush()  # Get module.id

            # Create lessons
            for lesson_data in lessons_data:
                lesson = Lesson(module_id=module.id, **lesson_data)
                db.add(lesson)

        db.commit()
        db.refresh(course)
        created_courses.append(course)

        print(f"✅ Created course: {course.title} (ID: {course.id})")
        print(f"   📚 {len(modules_data)} modules")

    return created_courses


def main():
    """Main seeder function"""
    print("🌱 Starting database seeder...\n")

    db = SessionLocal()
    try:
        # Create instructor
        instructor = create_sample_instructor(db)

        print()

        # Create courses
        courses = create_sample_courses(db, instructor.id)

        print(f"\n✅ Seeding complete! Created {len(courses)} courses")
        print("\n📝 Test Credentials:")
        print("   Instructor: instructor@test.com / password123")
        print("\n🔗 Visit http://localhost:3000/lms/courses to see the courses")

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
