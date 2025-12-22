from sqlalchemy.orm import Session
from app.models.course import Course
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_lower_string


def create_random_course(db: Session, instructor_id: int = None) -> Course:
    if not instructor_id:
        user = create_random_user(db)
        instructor_id = user.id

    title = random_lower_string()
    description = random_lower_string()

    db_obj = Course(
        title=title,
        description=description,
        instructor_id=instructor_id,
        is_published=True,
        price=99.99,
        level="beginner",
        category_id=1,  # Assuming category 1 exists or is not enforced by FK in sqlite for tests
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
