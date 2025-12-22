"""
Collaborative Project Schemas
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.collaborative_project import ProjectStatus, ProjectRole


# --- Milestones ---
class MilestoneBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_completed: bool = False


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None


class MilestoneResponse(MilestoneBase):
    id: int
    project_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Submissions ---
class SubmissionBase(BaseModel):
    file_url: Optional[str] = None
    description: Optional[str] = None


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionGrade(BaseModel):
    grade: float
    feedback: Optional[str] = None


class SubmissionResponse(SubmissionBase):
    id: int
    project_id: int
    team_id: int
    submitted_at: datetime
    grade: Optional[float] = None
    feedback: Optional[str] = None
    graded_by: Optional[int] = None
    graded_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- Teams ---
class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    role: ProjectRole
    joined_at: datetime
    user_name: Optional[str] = None  # Populated manually or via relationship
    model_config = ConfigDict(from_attributes=True)


class TeamBase(BaseModel):
    name: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamResponse(TeamBase):
    id: int
    project_id: int
    created_at: datetime
    members: List[TeamMemberResponse] = []
    submissions: List[SubmissionResponse] = []
    model_config = ConfigDict(from_attributes=True)


# --- Projects ---
class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    max_team_size: int = 5
    status: ProjectStatus = ProjectStatus.PLANNING


class ProjectCreate(ProjectBase):
    course_id: Optional[int] = None
    group_id: Optional[int] = None
    milestones: List[MilestoneCreate] = []


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[ProjectStatus] = None
    max_team_size: Optional[int] = None


class ProjectResponse(ProjectBase):
    id: int
    course_id: Optional[int]
    group_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    milestones: List[MilestoneResponse] = []
    teams: List[TeamResponse] = []
    model_config = ConfigDict(from_attributes=True)
