import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import Base
from app.models.user import User
from app.schemas.course import CourseCreate
from app.crud import course as crud_course

# Setup DB
import time

db_file = f"test_debug_course_{int(time.time())}.db"
url = f"sqlite:///./{db_file}"
engine = create_engine(url)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Create instructor
    instructor = User(email="inst@test.com", hashed_password="pw", role="instructor")
    db.add(instructor)
    db.commit()
    db.refresh(instructor)

    # Create course data (mimicking test_create_course_instructor_only)
    course_data = {
        "title": "Advanced Python",
        "description": "For experienced developers",
        "category_id": 1,  # Dummy
        "level": "advanced",
        "price": 1999.0,
        "is_published": False,
    }

    print(f"Creating course with data: {course_data}")

    # Create schema object
    course_in = CourseCreate(**course_data)

    # Call CRUD
    print("Calling crud_course.create_with_instructor...")
    course = crud_course.course.create_with_instructor(
        db=db, obj_in=course_in, instructor_id=instructor.id
    )

    print(f"Course created successfully! ID: {course.id}")
    print(f"Slug: {course.slug}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()
finally:
    db.close()
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except:
            pass
