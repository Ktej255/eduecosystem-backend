"""
Collaborative Project Models
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Enum,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base


class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"
    COMPLETED = "completed"


class ProjectRole(str, enum.Enum):
    LEADER = "leader"
    MEMBER = "member"


class CollaborativeProject(Base):
    __tablename__ = "collaborative_projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True
    )
    group_id = Column(
        Integer, ForeignKey("learning_groups.id", ondelete="CASCADE"), nullable=True
    )
    deadline = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PLANNING, nullable=False)
    max_team_size = Column(Integer, default=5)

    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    course = relationship("Course")
    group = relationship("LearningGroup")
    creator = relationship("User", foreign_keys=[created_by])
    teams = relationship(
        "ProjectTeam", back_populates="project", cascade="all, delete-orphan"
    )
    milestones = relationship(
        "ProjectMilestone", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectTeam(Base):
    __tablename__ = "project_teams"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("collaborative_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    project = relationship("CollaborativeProject", back_populates="teams")
    members = relationship(
        "ProjectTeamMember", back_populates="team", cascade="all, delete-orphan"
    )
    submissions = relationship(
        "ProjectSubmission", back_populates="team", cascade="all, delete-orphan"
    )


class ProjectTeamMember(Base):
    __tablename__ = "project_team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(
        Integer, ForeignKey("project_teams.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(Enum(ProjectRole), default=ProjectRole.MEMBER, nullable=False)
    joined_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    team = relationship("ProjectTeam", back_populates="members")
    user = relationship("User")


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("collaborative_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    project = relationship("CollaborativeProject", back_populates="milestones")


class ProjectSubmission(Base):
    __tablename__ = "project_submissions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("collaborative_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id = Column(
        Integer, ForeignKey("project_teams.id", ondelete="CASCADE"), nullable=False
    )
    file_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    submitted_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    grade = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    graded_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    graded_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    team = relationship("ProjectTeam", back_populates="submissions")
    grader = relationship("User", foreign_keys=[graded_by])
