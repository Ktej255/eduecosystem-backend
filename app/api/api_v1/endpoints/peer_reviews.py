from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.crud import peer_review as crud_pr
from app.crud import permissions as crud_permissions
from app.schemas.peer_review import (
    PeerReview,
    PeerReviewCreate,
    PeerReviewAssignment,
    PeerReviewAssignmentCreate,
)

router = APIRouter()

# ============================================================================
# PEER REVIEW ASSIGNMENTS
# ============================================================================


@router.get("/assignments/to-review", response_model=List[PeerReviewAssignment])
def list_reviews_to_give(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Get list of peer reviews assigned to the current user"""
    return crud_pr.peer_review_assignment.get_by_reviewer(
        db, reviewer_id=current_user.id, skip=skip, limit=limit
    )


@router.get("/assignments/received", response_model=List[PeerReviewAssignment])
def list_reviews_received(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Get list of peer reviews received by the current user"""
    return crud_pr.peer_review_assignment.get_by_reviewee(
        db, reviewee_id=current_user.id, skip=skip, limit=limit
    )


@router.post(
    "/assignments",
    response_model=PeerReviewAssignment,
    status_code=status.HTTP_201_CREATED,
)
def create_peer_review_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assignment_in: PeerReviewAssignmentCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Assign a peer review (Instructor only)"""
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "create_peer_review"
        ):
            raise HTTPException(
                status_code=403, detail="Permission denied: create_peer_review required"
            )

    return crud_pr.peer_review_assignment.create(db, obj_in=assignment_in)


# ============================================================================
# PEER REVIEWS
# ============================================================================


@router.post("/", response_model=PeerReview, status_code=status.HTTP_201_CREATED)
def submit_peer_review(
    *,
    db: Session = Depends(deps.get_db),
    review_in: PeerReviewCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Submit a peer review"""
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "submit_peer_review"
        ):
            raise HTTPException(
                status_code=403, detail="Permission denied: submit_peer_review required"
            )

    # Verify assignment belongs to user
    assignment = crud_pr.peer_review_assignment.get(
        db, id=review_in.peer_review_assignment_id
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.reviewer_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to submit this review"
        )

    if assignment.status == "submitted":
        raise HTTPException(status_code=400, detail="Review already submitted")

    review = crud_pr.peer_review.create_with_assignment(db, obj_in=review_in)

    # Award coins for completing peer review
    try:
        from app.services.coin_service import trigger_coin_reward

        trigger_coin_reward(
            db=db,
            user=current_user,
            action="peer_review_submit",
            reference_type="peer_review",
            reference_id=review.id,
            description="Completed peer review",
        )
    except Exception as e:
        print(f"Failed to award coins for peer review: {e}")

    return review


@router.get("/{review_id}", response_model=PeerReview)
def get_peer_review(
    review_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get a specific peer review"""
    review = crud_pr.peer_review.get(db, id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Check permissions (reviewer, reviewee, or instructor)
    assignment = review.assignment_link
    is_involved = (
        assignment.reviewer_id == current_user.id
        or assignment.reviewee_id == current_user.id
    )

    if not is_involved and not current_user.is_superuser:
        # Check if instructor
        if not crud_permissions.check_role(db, current_user.id, "instructor"):
            raise HTTPException(status_code=403, detail="Not authorized")

    return review
