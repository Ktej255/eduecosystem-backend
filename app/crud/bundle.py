from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.bundle import CourseBundle
from app.models.course import Course
from app.schemas.bundle import BundleCreate, BundleUpdate


class CRUDCourseBundle:
    def get(self, db: Session, id: int) -> Optional[CourseBundle]:
        return db.query(CourseBundle).filter(CourseBundle.id == id).first()

    def get_multi(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[CourseBundle]:
        return (
            db.query(CourseBundle)
            .filter(CourseBundle.is_published == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_instructor(
        self, db: Session, instructor_id: int, skip: int = 0, limit: int = 100
    ) -> List[CourseBundle]:
        return (
            db.query(CourseBundle)
            .filter(CourseBundle.instructor_id == instructor_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(
        self, db: Session, *, obj_in: BundleCreate, instructor_id: int
    ) -> CourseBundle:
        db_obj = CourseBundle(
            title=obj_in.title,
            description=obj_in.description,
            price=obj_in.price,
            currency=obj_in.currency,
            thumbnail_url=obj_in.thumbnail_url,
            is_published=obj_in.is_published,
            instructor_id=instructor_id,
        )

        # Add courses
        if obj_in.course_ids:
            courses = db.query(Course).filter(Course.id.in_(obj_in.course_ids)).all()
            db_obj.courses = courses

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: CourseBundle, obj_in: BundleUpdate
    ) -> CourseBundle:
        update_data = obj_in.dict(exclude_unset=True)

        # Handle courses update separately
        if "course_ids" in update_data:
            course_ids = update_data.pop("course_ids")
            courses = db.query(Course).filter(Course.id.in_(course_ids)).all()
            db_obj.courses = courses

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> CourseBundle:
        obj = db.query(CourseBundle).get(id)
        db.delete(obj)
        db.commit()
        return obj


bundle = CRUDCourseBundle()
