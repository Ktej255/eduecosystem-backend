"""
Collaborative Projects API Endpoints
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.models.user import User
from app.models.collaborative_project import (
    CollaborativeProject,
    ProjectTeam,
    ProjectTeamMember,
    ProjectMilestone,
    ProjectSubmission,
    ProjectStatus,
    ProjectRole,
)
from app.schemas.collaborative_project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    TeamCreate,
    TeamResponse,
    SubmissionCreate,
    SubmissionGrade,
    SubmissionResponse,
)

router = APIRouter()

# --- Projects ---


@router.post("/", response_model=ProjectResponse)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new collaborative project"""
    project = CollaborativeProject(
        title=project_in.title,
        description=project_in.description,
        course_id=project_in.course_id,
        group_id=project_in.group_id,
        deadline=project_in.deadline,
        status=project_in.status,
        max_team_size=project_in.max_team_size,
        created_by=current_user.id,
    )
    db.add(project)
    db.flush()  # Get ID

    for m in project_in.milestones:
        milestone = ProjectMilestone(
            project_id=project.id,
            title=m.title,
            description=m.description,
            due_date=m.due_date,
            is_completed=m.is_completed,
        )
        db.add(milestone)

    db.commit()
    db.refresh(project)
    return project


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    course_id: Optional[int] = None,
    group_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """List projects"""
    query = db.query(CollaborativeProject)
    if course_id:
        query = query.filter(CollaborativeProject.course_id == course_id)
    if group_id:
        query = query.filter(CollaborativeProject.group_id == group_id)

    projects = query.offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get project details"""
    project = (
        db.query(CollaborativeProject)
        .filter(CollaborativeProject.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update project"""
    project = (
        db.query(CollaborativeProject)
        .filter(CollaborativeProject.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check permissions (creator or admin)
    if project.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


# --- Teams ---


@router.post("/{project_id}/teams", response_model=TeamResponse)
def create_team(
    project_id: int,
    team_in: TeamCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a team for a project"""
    project = (
        db.query(CollaborativeProject)
        .filter(CollaborativeProject.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    team = ProjectTeam(project_id=project_id, name=team_in.name)
    db.add(team)
    db.flush()

    # Add creator as leader
    member = ProjectTeamMember(
        team_id=team.id, user_id=current_user.id, role=ProjectRole.LEADER
    )
    db.add(member)
    db.commit()
    db.refresh(team)
    return team


@router.post("/{project_id}/teams/{team_id}/join")
def join_team(
    project_id: int,
    team_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Join a project team"""
    team = (
        db.query(ProjectTeam)
        .filter(ProjectTeam.id == team_id, ProjectTeam.project_id == project_id)
        .first()
    )
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if already in a team for this project
    existing_membership = (
        db.query(ProjectTeamMember)
        .join(ProjectTeam)
        .filter(
            ProjectTeam.project_id == project_id,
            ProjectTeamMember.user_id == current_user.id,
        )
        .first()
    )

    if existing_membership:
        raise HTTPException(
            status_code=400, detail="Already in a team for this project"
        )

    # Check max size
    if len(team.members) >= team.project.max_team_size:
        raise HTTPException(status_code=400, detail="Team is full")

    member = ProjectTeamMember(
        team_id=team_id, user_id=current_user.id, role=ProjectRole.MEMBER
    )
    db.add(member)
    db.commit()
    return {"message": "Joined team successfully"}


# --- Submissions ---


@router.post("/{project_id}/teams/{team_id}/submit", response_model=SubmissionResponse)
def submit_project(
    project_id: int,
    team_id: int,
    submission_in: SubmissionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Submit project work"""
    # Verify user is in team
    member = (
        db.query(ProjectTeamMember)
        .filter(
            ProjectTeamMember.team_id == team_id,
            ProjectTeamMember.user_id == current_user.id,
        )
        .first()
    )

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    submission = ProjectSubmission(
        project_id=project_id,
        team_id=team_id,
        file_url=submission_in.file_url,
        description=submission_in.description,
    )
    db.add(submission)

    # Update project status if needed
    project = (
        db.query(CollaborativeProject)
        .filter(CollaborativeProject.id == project_id)
        .first()
    )
    if project.status != ProjectStatus.COMPLETED:
        project.status = ProjectStatus.SUBMITTED

    db.commit()
    db.refresh(submission)
    return submission


@router.post(
    "/{project_id}/submissions/{submission_id}/grade", response_model=SubmissionResponse
)
def grade_submission(
    project_id: int,
    submission_id: int,
    grade_in: SubmissionGrade,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Grade a submission"""
    submission = (
        db.query(ProjectSubmission)
        .filter(
            ProjectSubmission.id == submission_id,
            ProjectSubmission.project_id == project_id,
        )
        .first()
    )

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Verify grader permissions (project creator or admin)
    project = submission.team.project
    if project.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to grade")

    submission.grade = grade_in.grade
    submission.feedback = grade_in.feedback
    submission.graded_by = current_user.id
    submission.graded_at = datetime.utcnow()

    db.commit()
    db.refresh(submission)
    return submission
