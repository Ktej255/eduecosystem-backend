from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.tests.utils.course import create_random_course
from app.tests.utils.utils import random_lower_string


def create_random_assignment(db: Session, course_id: int = None) -> Assignment:
    if not course_id:
        course = create_random_course(db)
        course_id = course.id

    title = random_lower_string()
    description = random_lower_string()

    db_obj = Assignment(
        title=title,
        description=description,
        course_id=course_id,
        max_points=100.0,
        is_published=True,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
