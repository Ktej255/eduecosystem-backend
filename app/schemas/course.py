from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum
from .category import Category, Tag


# Enums
class CourseLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseCategory(str, Enum):
    PROGRAMMING = "programming"
    DATA_SCIENCE = "data_science"
    DESIGN = "design"
    BUSINESS = "business"
    MARKETING = "marketing"
    PERSONAL_DEVELOPMENT = "personal_development"
    HEALTH = "health"
    LANGUAGE = "language"
    OTHER = "other"


class LessonType(str, Enum):
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    INTERACTIVE = "interactive"
    LIVE_CLASS = "live_class"
    DOWNLOAD = "download"


class ProgressStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class EnrollmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    EXPIRED = "expired"


# ============================================================================
# COURSE SCHEMAS
# ============================================================================


class CourseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    long_description: Optional[str] = None
    # category: CourseCategory = CourseCategory.OTHER # Deprecated
    category_id: Optional[int] = None
    level: CourseLevel = CourseLevel.BEGINNER
    # tags: List[str] = Field(default_factory=list) # Deprecated
    thumbnail_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    price: float = Field(default=0.0, ge=0)
    currency: str = "USD"
    prerequisites: List[str] = Field(default_factory=list)
    is_published: bool = False
    is_featured: bool = False
    is_password_protected: bool = False


class CourseCreate(CourseBase):
    """Schema for creating a new course"""

    tag_ids: List[int] = Field(default_factory=list)
    password: Optional[str] = None


class CourseUpdate(BaseModel):
    """Schema for updating a course - all fields optional"""

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    long_description: Optional[str] = None
    category_id: Optional[int] = None
    level: Optional[CourseLevel] = None
    tag_ids: Optional[List[int]] = None
    thumbnail_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    prerequisite_lesson_ids: List[int] = Field(default_factory=list)
    duration_minutes: int = Field(default=0, ge=0)
    is_password_protected: Optional[bool] = None
    password: Optional[str] = None


class CourseInDBBase(CourseBase):
    id: int
    instructor_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Course(CourseInDBBase):
    """Full course schema"""

    category: Optional[Category] = None
    tags: List[Tag] = []


class CourseListItem(CourseInDBBase):
    """Course schema for list views"""

    category: Optional[Category] = None
    tags: List[Tag] = []
    total_students: int = 0
    average_rating: float = 0.0


class CourseWithModules(Course):
    """Course with nested modules and lessons"""

    modules: List["ModuleWithLessons"] = []


# ============================================================================
# MODULE SCHEMAS
# ============================================================================


class ModuleBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    order_index: int = Field(default=0, ge=0)


class ModuleCreate(ModuleBase):
    """Schema for creating a module"""

    course_id: Optional[int] = None


class ModuleUpdate(BaseModel):
    """Schema for updating a module"""

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)


class ModuleInDBBase(ModuleBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Module(ModuleInDBBase):
    """Full module schema"""

    pass


class ModuleWithLessons(Module):
    """Module with nested lessons"""

    lessons: List["Lesson"] = []


# ============================================================================
# LESSON SCHEMAS
# ============================================================================


class LessonBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    type: LessonType = LessonType.TEXT
    content: Optional[Any] = None
    video_url: Optional[str] = None
    video_duration_seconds: Optional[int] = Field(None, ge=0)
    attachments: List[dict] = Field(default_factory=list)
    order_index: int = Field(default=0, ge=0)
    is_preview: bool = False
    available_after_days: int = Field(default=0, ge=0)
    prerequisite_lesson_ids: List[int] = Field(default_factory=list)
    duration_minutes: int = Field(default=0, ge=0)


class LessonCreate(LessonBase):
    """Schema for creating a lesson"""

    pass


class LessonUpdate(BaseModel):
    """Schema for updating a lesson - all fields optional"""

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    type: Optional[LessonType] = None
    content: Optional[dict] = None
    video_url: Optional[str] = None
    video_duration_seconds: Optional[int] = Field(None, ge=0)
    attachments: Optional[List[dict]] = None
    order_index: Optional[int] = Field(None, ge=0)
    is_preview: Optional[bool] = None
    available_after_days: Optional[int] = Field(None, ge=0)
    prerequisite_lesson_ids: Optional[List[int]] = None
    duration_minutes: Optional[int] = Field(None, ge=0)


class LessonInDBBase(LessonBase):
    id: int
    module_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Lesson(LessonInDBBase):
    """Full lesson schema"""

    pass


# ============================================================================
# ENROLLMENT SCHEMAS
# ============================================================================


class EnrollmentBase(BaseModel):
    status: EnrollmentStatus = EnrollmentStatus.ACTIVE


class EnrollmentCreate(BaseModel):
    """Schema for enrolling in a course"""

    course_id: int


class EnrollmentUpdate(BaseModel):
    """Schema for updating enrollment"""

    status: Optional[EnrollmentStatus] = None
    last_accessed_lesson_id: Optional[int] = None


class EnrollmentInDBBase(EnrollmentBase):
    id: int
    user_id: int
    course_id: int
    progress_percentage: float = 0.0
    last_accessed_lesson_id: Optional[int] = None
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    last_accessed_at: datetime
    price_paid: float = 0.0
    certificate_issued: bool = False

    model_config = ConfigDict(from_attributes=True)


class Enrollment(EnrollmentInDBBase):
    """Full enrollment schema"""

    pass


class EnrollmentWithCourse(EnrollmentInDBBase):
    """Enrollment with course details"""

    course: CourseListItem


# ============================================================================
# LESSON PROGRESS SCHEMAS
# ============================================================================


class LessonProgressBase(BaseModel):
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    time_spent_seconds: int = Field(default=0, ge=0)
    video_progress_seconds: int = Field(default=0, ge=0)
    video_completed_percentage: float = Field(default=0.0, ge=0, le=100)
    result_data: dict = Field(default_factory=dict)


class LessonProgressCreate(BaseModel):
    """Schema for creating lesson progress"""

    lesson_id: int
    status: ProgressStatus = ProgressStatus.IN_PROGRESS


class LessonProgressUpdate(BaseModel):
    """Schema for updating lesson progress"""

    status: Optional[ProgressStatus] = None
    time_spent_seconds: Optional[int] = Field(None, ge=0)
    video_progress_seconds: Optional[int] = Field(None, ge=0)
    video_completed_percentage: Optional[float] = Field(None, ge=0, le=100)
    result_data: Optional[dict] = None


class LessonProgressInDBBase(LessonProgressBase):
    id: int
    user_id: int
    lesson_id: int
    first_accessed_at: datetime
    last_accessed_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LessonProgress(LessonProgressInDBBase):
    """Full lesson progress schema"""

    pass


# ============================================================================
# COURSE REVIEW SCHEMAS
# ============================================================================


class CourseReviewBase(BaseModel):
    rating: float = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=100)
    review_text: Optional[str] = None


class CourseReviewCreate(CourseReviewBase):
    """Schema for creating a review"""

    course_id: int


class CourseReviewUpdate(BaseModel):
    """Schema for updating a review"""

    rating: Optional[float] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=100)
    review_text: Optional[str] = None


class CourseReviewInDBBase(CourseReviewBase):
    id: int
    course_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    is_approved: int = 1
    helpful_count: int = 0
    has_found_helpful: bool = False
    author_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourseReview(CourseReviewInDBBase):
    """Full review schema"""

    pass
