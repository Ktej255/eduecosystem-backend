from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.crud import student_notes as crud_notes
from app.schemas.student_notes import (
    Note,
    NoteCreate,
    NoteUpdate,
    NoteListItem,
    LessonBookmark,
    LessonBookmarkCreate,
    CourseBookmark,
    CourseBookmarkCreate,
    StudentNotesAndBookmarks,
)

router = APIRouter()


# ============================================================================
# NOTE ENDPOINTS
# ============================================================================


@router.get("/search", response_model=List[NoteListItem])
def search_notes(
    query: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=50, le=100),
) -> Any:
    """Search notes by content"""
    notes = crud_notes.note.search_notes(
        db, user_id=current_user.id, query=query, skip=skip, limit=limit
    )

    result = []
    for note in notes:
        note_dict = {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "timestamp": note.timestamp,
            "color": note.color,
            "created_at": note.created_at,
            "lesson_title": note.lesson.title if note.lesson else None,
            "course_title": note.lesson.module.course.title
            if (note.lesson and note.lesson.module and note.lesson.module.course)
            else None,
        }
        result.append(note_dict)

    return result


@router.get("/lessons/{lesson_id}/notes", response_model=List[Note])
def get_lesson_notes(
    lesson_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all notes for a specific lesson"""
    notes = crud_notes.note.get_by_lesson(
        db, lesson_id=lesson_id, user_id=current_user.id
    )

    # Enhance with lesson info
    result = []
    for note in notes:
        note_dict = Note.from_orm(note).model_dump()
        if note.lesson:
            note_dict["lesson_title"] = note.lesson.title
        result.append(note_dict)

    return result


@router.get("/courses/{course_id}/notes", response_model=List[NoteListItem])
def get_course_notes(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
) -> Any:
    """Get all notes for a course"""
    notes = crud_notes.note.get_by_course(
        db, course_id=course_id, user_id=current_user.id, skip=skip, limit=limit
    )

    # Enhance with info
    result = []
    for note in notes:
        note_dict = NoteListItem.from_orm(note).model_dump()
        if note.lesson:
            note_dict["lesson_title"] = note.lesson.title
            if note.lesson.module:
                note_dict["course_title"] = (
                    note.lesson.module.course.title if note.lesson.module.course else ""
                )
        result.append(note_dict)

    return result


@router.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
def create_note(
    *,
    db: Session = Depends(deps.get_db),
    note_in: NoteCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new note"""
    note = crud_notes.note.create_with_user(db, obj_in=note_in, user_id=current_user.id)
    return note


@router.put("/notes/{note_id}", response_model=Note)
def update_note(
    note_id: int,
    *,
    db: Session = Depends(deps.get_db),
    note_in: NoteUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a note"""
    note = crud_notes.note.get(db, id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    note = crud_notes.note.update(db, db_obj=note, obj_in=note_in)
    return note


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """Delete a note"""
    note = crud_notes.note.get(db, id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    crud_notes.note.remove(db, id=note_id)


# ============================================================================
# LESSON BOOKMARK ENDPOINTS
# ============================================================================


@router.get("/bookmarks/lessons", response_model=List[LessonBookmark])
def list_lesson_bookmarks(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
) -> Any:
    """Get all lesson bookmarks for current user"""
    bookmarks = crud_notes.lesson_bookmark.get_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )

    # Enhance with info
    result = []
    for bm in bookmarks:
        bm_dict = LessonBookmark.from_orm(bm).model_dump()
        if bm.lesson:
            bm_dict["lesson_title"] = bm.lesson.title
            if bm.lesson.module:
                bm_dict["module_title"] = bm.lesson.module.title
        if bm.course:
            bm_dict["course_title"] = bm.course.title
        result.append(bm_dict)

    return result


@router.post(
    "/bookmarks/lessons",
    response_model=LessonBookmark,
    status_code=status.HTTP_201_CREATED,
)
def bookmark_lesson(
    *,
    db: Session = Depends(deps.get_db),
    bookmark_in: LessonBookmarkCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Bookmark a lesson"""
    bookmark = crud_notes.lesson_bookmark.create(
        db, obj_in=bookmark_in, user_id=current_user.id
    )
    return bookmark


@router.delete("/bookmarks/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_lesson_bookmark(
    lesson_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """Remove a lesson bookmark"""
    success = crud_notes.lesson_bookmark.remove(
        db, lesson_id=lesson_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Bookmark not found")


@router.get("/lessons/{lesson_id}/is-bookmarked")
def check_lesson_bookmarked(
    lesson_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Check if lesson is bookmarked"""
    is_bookmarked = crud_notes.lesson_bookmark.is_bookmarked(
        db, lesson_id=lesson_id, user_id=current_user.id
    )
    return {"is_bookmarked": is_bookmarked}


# ============================================================================
# COURSE BOOKMARK ENDPOINTS
# ============================================================================


@router.get("/bookmarks/courses", response_model=List[CourseBookmark])
def list_course_bookmarks(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all course bookmarks for current user"""
    bookmarks = crud_notes.course_bookmark.get_by_user(db, user_id=current_user.id)

    # Enhance with info
    result = []
    for bm in bookmarks:
        bm_dict = CourseBookmark.from_orm(bm).model_dump()
        if bm.course:
            bm_dict["course_title"] = bm.course.title
            if bm.course.instructor:
                bm_dict["instructor_name"] = bm.course.instructor.full_name
        result.append(bm_dict)

    return result


@router.post(
    "/bookmarks/courses",
    response_model=CourseBookmark,
    status_code=status.HTTP_201_CREATED,
)
def bookmark_course(
    *,
    db: Session = Depends(deps.get_db),
    bookmark_in: CourseBookmarkCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Bookmark a course"""
    bookmark = crud_notes.course_bookmark.create(
        db, obj_in=bookmark_in, user_id=current_user.id
    )
    return bookmark


@router.delete("/bookmarks/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_course_bookmark(
    course_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """Remove a course bookmark"""
    success = crud_notes.course_bookmark.remove(
        db, course_id=course_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Bookmark not found")


@router.get("/courses/{course_id}/is-bookmarked")
def check_course_bookmarked(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Check if course is bookmarked"""
    is_bookmarked = crud_notes.course_bookmark.is_bookmarked(
        db, course_id=course_id, user_id=current_user.id
    )
    return {"is_bookmarked": is_bookmarked}


# ============================================================================
# AGGREGATE ENDPOINT
# ============================================================================


@router.get("/my-notes-and-bookmarks", response_model=StudentNotesAndBookmarks)
def get_my_notes_and_bookmarks(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all notes and bookmarks for current user"""
    notes = crud_notes.note.get_by_user(db, user_id=current_user.id, limit=1000)
    lesson_bookmarks = crud_notes.lesson_bookmark.get_by_user(
        db, user_id=current_user.id, limit=1000
    )
    course_bookmarks = crud_notes.course_bookmark.get_by_user(
        db, user_id=current_user.id, limit=1000
    )

    # Process notes
    note_list = []
    for note in notes:
        note_dict = NoteListItem.from_orm(note).model_dump()
        if note.lesson:
            note_dict["lesson_title"] = note.lesson.title
            if note.lesson.module and note.lesson.module.course:
                note_dict["course_title"] = note.lesson.module.course.title
        note_list.append(note_dict)

    # Process bookmarks
    lesson_bm_list = []
    for bm in lesson_bookmarks:
        bm_dict = LessonBookmark.from_orm(bm).model_dump()
        if bm.lesson:
            bm_dict["lesson_title"] = bm.lesson.title
        if bm.course:
            bm_dict["course_title"] = bm.course.title
        lesson_bm_list.append(bm_dict)

    course_bm_list = []
    for bm in course_bookmarks:
        bm_dict = CourseBookmark.from_orm(bm).model_dump()
        if bm.course:
            bm_dict["course_title"] = bm.course.title
            if bm.course.instructor:
                bm_dict["instructor_name"] = bm.course.instructor.full_name
        course_bm_list.append(bm_dict)

    return {
        "notes": note_list,
        "lesson_bookmarks": lesson_bm_list,
        "course_bookmarks": course_bm_list,
        "total_notes": len(note_list),
        "total_bookmarks": len(lesson_bm_list) + len(course_bm_list),
    }
