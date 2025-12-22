from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_

from app.crud.base import CRUDBase
from app.models.course import Course, CourseLevel
from app.models.module import Module
from app.models.lesson import Lesson
from app.models.category import Category, Tag
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    ModuleCreate,
    ModuleUpdate,
    LessonCreate,
    LessonUpdate,
    CourseReviewCreate,
    CourseReviewUpdate,
)
from app.models.course_review import CourseReview

from app.core.security import get_password_hash


class CRUDCourse(CRUDBase[Course, CourseCreate, CourseUpdate]):
    def get_by_instructor(
        self, db: Session, *, instructor_id: int, skip: int = 0, limit: int = 100
    ) -> List[Course]:
        return (
            db.query(Course)
            .filter(Course.instructor_id == instructor_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get(self, db: Session, id: Any) -> Optional[Course]:
        from sqlalchemy.orm import joinedload, selectinload

        return (
            db.query(Course)
            .options(
                joinedload(Course.category_rel),
                selectinload(Course.tags_rel),
                selectinload(Course.modules).selectinload(Module.lessons),
            )
            .filter(Course.id == id)
            .first()
        )

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        is_published: Optional[bool] = None,
        category_id: Optional[int] = None,
        level: Optional[CourseLevel] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
        sort_by: Optional[str] = "newest",
    ) -> List[Course]:
        from sqlalchemy.orm import joinedload, selectinload

        query = db.query(Course).options(
            joinedload(Course.category_rel), selectinload(Course.tags_rel)
        )

        # Filtering
        if is_published is not None:
            query = query.filter(Course.is_published == is_published)

        if category_id:
            query = query.filter(Course.category_id == category_id)

        if level:
            query = query.filter(Course.level == level)

        if min_price is not None:
            query = query.filter(Course.price >= min_price)

        if max_price is not None:
            query = query.filter(Course.price <= max_price)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Course.title.ilike(search_term),
                    Course.description.ilike(search_term),
                )
            )

        if tag_ids:
            query = query.filter(Course.tags_rel.any(Tag.id.in_(tag_ids)))

        # Sorting
        if sort_by == "price_asc":
            query = query.order_by(asc(Course.price))
        elif sort_by == "price_desc":
            query = query.order_by(desc(Course.price))
        elif sort_by == "rating":
            query = query.order_by(desc(Course.average_rating))
        elif sort_by == "popularity":
            query = query.order_by(desc(Course.total_enrollments))
        else:  # newest
            query = query.order_by(desc(Course.created_at))

        return query.offset(skip).limit(limit).all()

    def create_with_instructor(
        self, db: Session, *, obj_in: CourseCreate, instructor_id: int
    ) -> Course:
        obj_in_data = obj_in.dict(exclude={"tag_ids", "password"})
        tag_ids = obj_in.tag_ids

        # Generate slug if not provided
        if "slug" not in obj_in_data or not obj_in_data["slug"]:
            import re

            title = obj_in_data.get("title", "")
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            obj_in_data["slug"] = slug

        if obj_in.password:
            obj_in_data["password_hash"] = get_password_hash(obj_in.password)
            obj_in_data["is_password_protected"] = True

        db_obj = Course(**obj_in_data, instructor_id=instructor_id)

        if tag_ids:
            tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            db_obj.tags_rel = tags

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Course,
        obj_in: Union[CourseUpdate, Dict[str, Any]],
    ) -> Course:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        # Handle tags update
        if "tag_ids" in update_data:
            tag_ids = update_data.pop("tag_ids")
            if tag_ids is not None:
                tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
                db_obj.tags_rel = tags

        # Handle password update
        if "password" in update_data:
            password = update_data.pop("password")
            if password:
                update_data["password_hash"] = get_password_hash(password)
                update_data["is_password_protected"] = True
            elif password == "":  # Empty string means remove password
                update_data["password_hash"] = None
                update_data["is_password_protected"] = False

        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def create_from_import(
        self, db: Session, *, obj_in: dict, instructor_id: int
    ) -> Course:
        # Extract modules and tags
        modules_data = obj_in.pop("modules", [])
        tags_data = obj_in.pop("tags", [])
        category_slug = obj_in.pop("category_slug", None)

        # Handle category if slug provided
        if category_slug:
            category = db.query(Category).filter(Category.slug == category_slug).first()
            if category:
                obj_in["category_id"] = category.id

        # Create course
        db_obj = Course(**obj_in, instructor_id=instructor_id)

        # Handle tags
        if tags_data:
            tags = []
            for tag_name in tags_data:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name, slug=tag_name.lower().replace(" ", "-"))
                    db.add(tag)
                    db.flush()
                tags.append(tag)
            db_obj.tags_rel = tags

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Create modules and lessons
        from app.models.course import Module, Lesson

        for module_data in modules_data:
            lessons_data = module_data.pop("lessons", [])
            module = Module(**module_data, course_id=db_obj.id)
            db.add(module)
            db.commit()
            db.refresh(module)

            for lesson_data in lessons_data:
                lesson = Lesson(**lesson_data, module_id=module.id)
                db.add(lesson)

            db.commit()

        return db_obj


course = CRUDCourse(Course)


class CRUDModule(CRUDBase[Module, ModuleCreate, ModuleUpdate]):
    def create_with_course(
        self, db: Session, *, obj_in: ModuleCreate, course_id: int
    ) -> Module:
        obj_in_data = obj_in.dict(exclude={"course_id"})
        db_obj = Module(**obj_in_data, course_id=course_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_course(self, db: Session, *, course_id: int) -> List[Module]:
        return (
            db.query(Module)
            .filter(Module.course_id == course_id)
            .order_by(Module.order_index)
            .all()
        )


module = CRUDModule(Module)


class CRUDLesson(CRUDBase[Lesson, LessonCreate, LessonUpdate]):
    def create_with_module(
        self, db: Session, *, obj_in: LessonCreate, module_id: int
    ) -> Lesson:
        obj_in_data = obj_in.model_dump()
        db_obj = Lesson(**obj_in_data, module_id=module_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_module(self, db: Session, *, module_id: int) -> List[Lesson]:
        return (
            db.query(Lesson)
            .filter(Lesson.module_id == module_id)
            .order_by(Lesson.order_index)
            .all()
        )


lesson = CRUDLesson(Lesson)


class CRUDCourseReview(CRUDBase[CourseReview, CourseReviewCreate, CourseReviewUpdate]):
    def get_by_course(self, db: Session, *, course_id: int) -> List[CourseReview]:
        return db.query(CourseReview).filter(CourseReview.course_id == course_id).all()

    def create(
        self, db: Session, *, obj_in: CourseReviewCreate, user_id: int
    ) -> CourseReview:
        obj_in_data = obj_in.model_dump()
        db_obj = CourseReview(**obj_in_data, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


course_review = CRUDCourseReview(CourseReview)
