from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.course_review import CourseReview, ReviewHelpful
from app.schemas.course import CourseReviewUpdate, CourseReview as CourseReviewSchema

router = APIRouter()


@router.patch("/{review_id}", response_model=CourseReviewSchema)
def update_review(
    review_id: int,
    *,
    db: Session = Depends(deps.get_db),
    review_in: CourseReviewUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a review
    """
    review = db.query(CourseReview).filter(CourseReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = review_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    db.add(review)
    db.commit()
    db.refresh(review)

    # Populate author_name
    result = CourseReviewSchema.from_orm(review)
    if review.user:
        result.author_name = review.user.full_name

    return result


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete a review
    """
    review = db.query(CourseReview).filter(CourseReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(review)
    db.commit()


@router.post("/{review_id}/helpful")
def mark_review_helpful(
    review_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Mark a review as helpful
    """
    review = db.query(CourseReview).filter(CourseReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Check if already marked
    existing = (
        db.query(ReviewHelpful)
        .filter(
            ReviewHelpful.review_id == review_id,
            ReviewHelpful.user_id == current_user.id,
        )
        .first()
    )

    if existing:
        # Toggle off
        db.delete(existing)
        review.helpful_count = max(0, review.helpful_count - 1)
        message = "Removed helpful mark"
    else:
        # Toggle on
        helpful = ReviewHelpful(review_id=review_id, user_id=current_user.id)
        db.add(helpful)
        review.helpful_count += 1
        message = "Marked as helpful"

    db.add(review)
    db.commit()

    return {"message": message, "helpful_count": review.helpful_count}
