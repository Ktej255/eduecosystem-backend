"""
Social Learning Groups API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.api import deps
from app.models.user import User
from app.models.learning_group import (
    LearningGroup,
    GroupMembership,
    GroupPost,
    GroupType,
    GroupPrivacy,
    MemberRole,
)

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================


class GroupCreate(BaseModel):
    name: str
    description: str
    group_type: GroupType
    privacy: GroupPrivacy = GroupPrivacy.PUBLIC
    course_id: Optional[int] = None
    max_members: int = 50


class GroupResponse(BaseModel):
    id: int
    name: str
    description: str
    group_type: str
    privacy: str
    course_id: Optional[int]
    member_count: int
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostCreate(BaseModel):
    content: str


class PostResponse(BaseModel):
    id: int
    content: str
    author_name: str
    likes_count: int
    is_pinned: bool
    created_at: datetime
    comment_count: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# GROUP ENDPOINTS
# ============================================================================


@router.post("/groups", response_model=GroupResponse)
def create_group(
    group: GroupCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Create a new learning group"""
    new_group = LearningGroup(
        name=group.name,
        description=group.description,
        group_type=group.group_type,
        privacy=group.privacy,
        course_id=group.course_id,
        max_members=group.max_members,
        created_by=current_user.id,
    )
    db.add(new_group)
    db.flush()

    # Add creator as admin
    membership = GroupMembership(
        group_id=new_group.id, user_id=current_user.id, role=MemberRole.ADMIN
    )
    db.add(membership)
    db.commit()
    db.refresh(new_group)

    return {**new_group.__dict__, "member_count": 1}


@router.get("/groups", response_model=List[GroupResponse])
def list_groups(
    group_type: Optional[GroupType] = None,
    course_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
):
    """List all public learning groups"""
    query = db.query(LearningGroup).filter(
        LearningGroup.is_active == True, LearningGroup.privacy == GroupPrivacy.PUBLIC
    )

    if group_type:
        query = query.filter(LearningGroup.group_type == group_type)
    if course_id:
        query = query.filter(LearningGroup.course_id == course_id)

    groups = query.offset(skip).limit(limit).all()

    return [{**group.__dict__, "member_count": len(group.members)} for group in groups]


@router.get("/groups/my", response_model=List[GroupResponse])
def list_my_groups(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List groups the current user is a member of"""
    groups = (
        db.query(LearningGroup)
        .join(GroupMembership)
        .filter(GroupMembership.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [{**group.__dict__, "member_count": len(group.members)} for group in groups]


@router.post("/groups/{group_id}/join")
def join_group(
    group_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Join a learning group"""
    group = db.query(LearningGroup).filter(LearningGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if already a member
    existing = (
        db.query(GroupMembership)
        .filter(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == current_user.id,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Already a member")

    # Check max members
    if len(group.members) >= group.max_members:
        raise HTTPException(status_code=400, detail="Group is full")

    # Add membership
    membership = GroupMembership(
        group_id=group_id, user_id=current_user.id, role=MemberRole.MEMBER
    )
    db.add(membership)
    db.commit()

    return {"message": "Joined group successfully"}


@router.post("/groups/{group_id}/leave")
def leave_group(
    group_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Leave a learning group"""
    membership = (
        db.query(GroupMembership)
        .filter(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == current_user.id,
        )
        .first()
    )

    if not membership:
        raise HTTPException(status_code=404, detail="Not a member")

    db.delete(membership)
    db.commit()

    return {"message": "Left group successfully"}


# ============================================================================
# GROUP POSTS
# ============================================================================


@router.post("/groups/{group_id}/posts", response_model=PostResponse)
def create_post(
    group_id: int,
    post: PostCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Create a post in a learning group"""
    # Check membership
    membership = (
        db.query(GroupMembership)
        .filter(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == current_user.id,
        )
        .first()
    )

    if not membership:
        raise HTTPException(status_code=403, detail="Not a group member")

    new_post = GroupPost(
        group_id=group_id, user_id=current_user.id, content=post.content
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return {
        "id": new_post.id,
        "content": new_post.content,
        "author_name": current_user.full_name or current_user.email,
        "likes_count": 0,
        "is_pinned": False,
        "created_at": new_post.created_at,
        "comment_count": 0,
    }


@router.get("/groups/{group_id}/posts", response_model=List[PostResponse])
def get_group_posts(
    group_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get posts from a learning group"""
    # Check membership
    membership = (
        db.query(GroupMembership)
        .filter(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == current_user.id,
        )
        .first()
    )

    if not membership:
        raise HTTPException(status_code=403, detail="Not a group member")

    posts = (
        db.query(GroupPost)
        .filter(GroupPost.group_id == group_id)
        .order_by(GroupPost.is_pinned.desc(), GroupPost.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": post.id,
            "content": post.content,
            "author_name": post.author.full_name or post.author.email,
            "likes_count": post.likes_count,
            "is_pinned": post.is_pinned,
            "created_at": post.created_at,
            "comment_count": len(post.comments),
        }
        for post in posts
    ]
