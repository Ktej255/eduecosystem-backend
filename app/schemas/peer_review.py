from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.user import UserBasic

# ============================================================================
# PEER REVIEW ASSIGNMENT SCHEMAS
# ============================================================================


class PeerReviewAssignmentBase(BaseModel):
    assignment_id: int
    reviewer_id: int
    reviewee_id: int
    submission_id: int
    due_date: Optional[datetime] = None


class PeerReviewAssignmentCreate(PeerReviewAssignmentBase):
    pass


class PeerReviewAssignmentUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[datetime] = None


class PeerReviewAssignmentInDBBase(PeerReviewAssignmentBase):
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PeerReviewAssignment(PeerReviewAssignmentInDBBase):
    reviewer: Optional[UserBasic] = None
    reviewee: Optional[UserBasic] = None


# ============================================================================
# PEER REVIEW SCHEMAS
# ============================================================================


class PeerReviewBase(BaseModel):
    content: str = Field(..., min_length=10)
    score: Optional[float] = Field(None, ge=0, le=100)


class PeerReviewCreate(PeerReviewBase):
    peer_review_assignment_id: int


class PeerReviewUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=10)
    score: Optional[float] = Field(None, ge=0, le=100)


class PeerReviewInDBBase(PeerReviewBase):
    id: int
    peer_review_assignment_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PeerReview(PeerReviewInDBBase):
    pass
