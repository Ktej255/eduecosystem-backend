from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


# Base schemas
class LearningPathBase(BaseModel):
    title: str
    description: Optional[str] = None
    slug: Optional[str] = None
    thumbnail_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    difficulty_level: str = "beginner"
    estimated_duration_hours: Optional[int] = None
    price: float = 0.0
    is_published: bool = False


class LearningPathCreate(LearningPathBase):
    pass


class LearningPathUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    thumbnail_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration_hours: Optional[int] = None
    price: Optional[float] = None
    is_published: Optional[bool] = None


class LearningPath(LearningPathBase):
    id: int
    creator_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# PathCourse schemas
class PathCourseBase(BaseModel):
    course_id: int
    order_index: int = 0
    prerequisite_course_id: Optional[int] = None
    is_required: bool = True


class PathCourseCreate(PathCourseBase):
    path_id: int


class PathCourseUpdate(BaseModel):
    order_index: Optional[int] = None
    prerequisite_course_id: Optional[int] = None
    is_required: Optional[bool] = None


class PathCourse(PathCourseBase):
    id: int
    path_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# PathEnrollment schemas
class PathEnrollmentBase(BaseModel):
    path_id: int


class PathEnrollmentCreate(PathEnrollmentBase):
    pass


class PathEnrollmentUpdate(BaseModel):
    current_course_id: Optional[int] = None
    completed_courses: Optional[int] = None
    total_courses: Optional[int] = None
    progress_percentage: Optional[float] = None
    is_completed: Optional[bool] = None


class PathEnrollment(PathEnrollmentBase):
    id: int
    student_id: int
    current_course_id: Optional[int] = None
    completed_courses: int
    total_courses: int
    progress_percentage: float
    is_completed: bool
    completed_at: Optional[datetime] = None
    has_paid: bool
    payment_id: Optional[int] = None
    enrolled_at: datetime
    last_accessed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Extended schemas with relationships
class LearningPathWithCourses(LearningPath):
    """Learning path with its courses"""

    path_courses: List[PathCourse] = []
    total_enrollments: int = 0


class PathEnrollmentWithProgress(PathEnrollment):
    """Enrollment with path details"""

    path: Optional[LearningPath] = None


class LearningPathList(BaseModel):
    """Paginated list of learning paths"""

    items: List[LearningPath]
    total: int
    page: int
    page_size: int
