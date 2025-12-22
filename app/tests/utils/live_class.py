from sqlalchemy.orm import Session
from app.models.live_class import LiveClass, LiveClassStatus
from app.tests.utils.user import create_random_user
from app.tests.utils.course import create_random_course
from app.tests.utils.utils import random_lower_string
from datetime import datetime, timedelta


def create_random_live_class(
    db: Session, course_id: int = None, instructor_id: int = None
) -> LiveClass:
    if not course_id:
        course = create_random_course(db)
        course_id = course.id
    if not instructor_id:
        user = create_random_user(db)
        instructor_id = user.id

    title = random_lower_string()
    description = random_lower_string()
    scheduled_at = datetime.utcnow() + timedelta(days=1)

    db_obj = LiveClass(
        course_id=course_id,
        instructor_id=instructor_id,
        title=title,
        description=description,
        scheduled_at=scheduled_at,
        status=LiveClassStatus.SCHEDULED,
        platform="zoom",
        meeting_url="https://zoom.us/j/123456789",
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
