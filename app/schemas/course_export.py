from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.course import CourseBase


class LessonExport(BaseModel):
    title: str
    description: Optional[str] = None
    type: str
    content: Optional[dict] = None
    video_url: Optional[str] = None
    duration_minutes: int = 0
    is_preview: bool = False
    order_index: int


class ModuleExport(BaseModel):
    title: str
    description: Optional[str] = None
    order_index: int
    lessons: List[LessonExport] = []


class CourseExport(CourseBase):
    modules: List[ModuleExport] = []
    category_slug: Optional[str] = None
    tags: List[str] = []

    model_config = ConfigDict(from_attributes=True)
