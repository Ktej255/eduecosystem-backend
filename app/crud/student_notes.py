from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.crud.base import CRUDBase
from app.models.student_notes import LessonNote, LessonBookmark, CourseBookmark
from app.models.lesson import Lesson
from app.models.module import Module
from app.schemas.student_notes import (
    NoteCreate,
    NoteUpdate,
    LessonBookmarkCreate,
    CourseBookmarkCreate,
)


class CRUDNote(CRUDBase[LessonNote, NoteCreate, NoteUpdate]):
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[LessonNote]:
        """Get all notes for a user"""
        return (
            db.query(LessonNote)
            .filter(LessonNote.user_id == user_id)
            .order_by(desc(LessonNote.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_lesson(
        self,
        db: Session,
        *,
        lesson_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[LessonNote]:
        """Get notes for a specific lesson by user"""
        return (
            db.query(LessonNote)
            .filter(LessonNote.lesson_id == lesson_id, LessonNote.user_id == user_id)
            .order_by(LessonNote.timestamp, desc(LessonNote.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_course(
        self,
        db: Session,
        *,
        course_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LessonNote]:
        """Get all notes for a course by user"""
        return (
            db.query(LessonNote)
            .join(Lesson)
            .join(Module)
            .filter(Module.course_id == course_id, LessonNote.user_id == user_id)
            .order_by(desc(LessonNote.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_user(
        self, db: Session, *, obj_in: NoteCreate, user_id: int
    ) -> LessonNote:
        """Create a new note"""
        db_obj = LessonNote(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def search_notes(
        self, db: Session, *, user_id: int, query: str, skip: int = 0, limit: int = 50
    ) -> List[LessonNote]:
        """Search user's notes by content"""
        search_term = f"%{query}%"
        return (
            db.query(LessonNote)
            .filter(
                LessonNote.user_id == user_id, LessonNote.content.ilike(search_term)
            )
            .order_by(desc(LessonNote.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )


class CRUDLessonBookmark:
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[LessonBookmark]:
        """Get all lesson bookmarks for a user"""
        return (
            db.query(LessonBookmark)
            .filter(LessonBookmark.user_id == user_id)
            .order_by(desc(LessonBookmark.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_course(
        self, db: Session, *, course_id: int, user_id: int
    ) -> List[LessonBookmark]:
        """Get lesson bookmarks for a specific course"""
        return (
            db.query(LessonBookmark)
            .filter(
                LessonBookmark.course_id == course_id, LessonBookmark.user_id == user_id
            )
            .order_by(desc(LessonBookmark.created_at))
            .all()
        )

    def is_bookmarked(self, db: Session, *, lesson_id: int, user_id: int) -> bool:
        """Check if lesson is bookmarked by user"""
        return (
            db.query(LessonBookmark)
            .filter(
                LessonBookmark.lesson_id == lesson_id, LessonBookmark.user_id == user_id
            )
            .first()
            is not None
        )

    def create(
        self, db: Session, *, obj_in: LessonBookmarkCreate, user_id: int
    ) -> LessonBookmark:
        """Create a bookmark"""
        # Check if already bookmarked
        existing = (
            db.query(LessonBookmark)
            .filter(
                LessonBookmark.lesson_id == obj_in.lesson_id,
                LessonBookmark.user_id == user_id,
            )
            .first()
        )

        if existing:
            return existing

        db_obj = LessonBookmark(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, lesson_id: int, user_id: int) -> bool:
        """Remove a bookmark"""
        bookmark = (
            db.query(LessonBookmark)
            .filter(
                LessonBookmark.lesson_id == lesson_id, LessonBookmark.user_id == user_id
            )
            .first()
        )

        if bookmark:
            db.delete(bookmark)
            db.commit()
            return True
        return False


class CRUDCourseBookmark:
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[CourseBookmark]:
        """Get all course bookmarks for a user"""
        return (
            db.query(CourseBookmark)
            .filter(CourseBookmark.user_id == user_id)
            .order_by(desc(CourseBookmark.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def is_bookmarked(self, db: Session, *, course_id: int, user_id: int) -> bool:
        """Check if course is bookmarked by user"""
        return (
            db.query(CourseBookmark)
            .filter(
                CourseBookmark.course_id == course_id, CourseBookmark.user_id == user_id
            )
            .first()
            is not None
        )

    def create(
        self, db: Session, *, obj_in: CourseBookmarkCreate, user_id: int
    ) -> CourseBookmark:
        """Create a course bookmark"""
        # Check if already bookmarked
        existing = (
            db.query(CourseBookmark)
            .filter(
                CourseBookmark.course_id == obj_in.course_id,
                CourseBookmark.user_id == user_id,
            )
            .first()
        )

        if existing:
            return existing

        db_obj = CourseBookmark(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, course_id: int, user_id: int) -> bool:
        """Remove a course bookmark"""
        bookmark = (
            db.query(CourseBookmark)
            .filter(
                CourseBookmark.course_id == course_id, CourseBookmark.user_id == user_id
            )
            .first()
        )

        if bookmark:
            db.delete(bookmark)
            db.commit()
            return True
        return False


# Create instances
note = CRUDNote(LessonNote)
lesson_bookmark = CRUDLessonBookmark()
course_bookmark = CRUDCourseBookmark()
