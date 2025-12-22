from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============================================================================
# LESSON NOTE SCHEMAS
# ============================================================================


class NoteBase(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1)
    timestamp: Optional[int] = Field(None, ge=0)  # Video timestamp in seconds
    color: str = Field(default="yellow", pattern="^(yellow|blue|green|red|purple)$")


class NoteCreate(NoteBase):
    """Schema for creating a note"""

    lesson_id: int


class NoteUpdate(BaseModel):
    """Schema for updating a note"""

    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    timestamp: Optional[int] = Field(None, ge=0)
    color: Optional[str] = Field(None, pattern="^(yellow|blue|green|red|purple)$")


class NoteInDBBase(NoteBase):
    id: int
    lesson_id: int
    user_id: int
    is_private: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Note(NoteInDBBase):
    """Full note schema"""

    lesson_title: Optional[str] = None
    course_title: Optional[str] = None
    module_title: Optional[str] = None


class NoteListItem(BaseModel):
    """Note schema for list views"""

    id: int
    title: Optional[str] = None
    content: str
    lesson_title: Optional[str] = None
    course_title: Optional[str] = None
    timestamp: Optional[int] = None
    color: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# LESSON BOOKMARK SCHEMAS
# ============================================================================


class LessonBookmarkBase(BaseModel):
    note: Optional[str] = None


class LessonBookmarkCreate(LessonBookmarkBase):
    """Schema for creating a lesson bookmark"""

    lesson_id: int
    course_id: int


class LessonBookmarkUpdate(BaseModel):
    """Schema for updating a bookmark"""

    note: Optional[str] = None


class LessonBookmarkInDBBase(LessonBookmarkBase):
    id: int
    lesson_id: int
    user_id: int
    course_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LessonBookmark(LessonBookmarkInDBBase):
    """Full lesson bookmark schema"""

    lesson_title: Optional[str] = None
    course_title: Optional[str] = None
    module_title: Optional[str] = None


# ============================================================================
# COURSE BOOKMARK SCHEMAS
# ============================================================================


class CourseBookmarkBase(BaseModel):
    note: Optional[str] = None


class CourseBookmarkCreate(CourseBookmarkBase):
    """Schema for creating a course bookmark"""

    course_id: int


class CourseBookmarkInDBBase(CourseBookmarkBase):
    id: int
    course_id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseBookmark(CourseBookmarkInDBBase):
    """Full course bookmark schema"""

    course_title: Optional[str] = None
    instructor_name: Optional[str] = None


# ============================================================================
# AGGREGATE SCHEMAS
# ============================================================================


class StudentNotesAndBookmarks(BaseModel):
    """Combined notes and bookmarks for a student"""

    notes: List[NoteListItem] = []
    lesson_bookmarks: List[LessonBookmark] = []
    course_bookmarks: List[CourseBookmark] = []
    total_notes: int = 0
    total_bookmarks: int = 0
