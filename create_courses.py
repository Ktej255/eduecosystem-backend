from app.db.session import SessionLocal
from app.models.course import Course, Module, Lesson
from app.models.user import User

db = SessionLocal()

# Create instructor
instructor = User(
    email="instructor@test.com",
    full_name="Dr. Sarah Johnson",
    hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OQGwHfN7L3ve",
    is_superuser=False,
    role="instructor",
    coins=100,
)
db.add(instructor)
db.commit()
db.refresh(instructor)

# Create Python course
course1 = Course(
    instructor_id=instructor.id,
    title="Introduction to Python Programming",
    description="Learn Python from scratch with hands-on projects",
    category="programming",
    level="beginner",
    price=0.0,
    is_published=True,
)
db.add(course1)
db.commit()
db.refresh(course1)

# Create module
module1 = Module(course_id=course1.id, title="Getting Started", order_index=0)
db.add(module1)
db.commit()
db.refresh(module1)

# Create lessons
lesson1 = Lesson(
    module_id=module1.id,
    title="What is Python?",
    content="Introduction to Python",
    duration_minutes=15,
    order_index=0,
)
lesson2 = Lesson(
    module_id=module1.id,
    title="Installing Python",
    content="How to install Python",
    duration_minutes=10,
    order_index=1,
)
db.add_all([lesson1, lesson2])
db.commit()

# Create React course
course2 = Course(
    instructor_id=instructor.id,
    title="Web Development with React",
    description="Build modern web applications",
    category="programming",
    level="intermediate",
    price=49.99,
    is_published=True,
)
db.add(course2)
db.commit()

# Create Data Science course
course3 = Course(
    instructor_id=instructor.id,
    title="Data Science with Python",
    description="Master data analysis and machine learning",
    category="data_science",
    level="intermediate",
    price=79.99,
    is_published=True,
)
db.add(course3)
db.commit()

db.close()
print("✅ Created 3 courses successfully!")
