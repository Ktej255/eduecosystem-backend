from typing import List
from sqlalchemy.orm import Session
from app.models.submission import HandwritingSubmission
from app.schemas.submission import SubmissionCreate


def get_multi_by_owner(
    db: Session, *, user_id: int, skip: int = 0, limit: int = 100
) -> List[HandwritingSubmission]:
    return (
        db.query(HandwritingSubmission)
        .filter(HandwritingSubmission.user_id == user_id)
        .order_by(HandwritingSubmission.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_with_owner(
    db: Session, *, obj_in: SubmissionCreate, owner_id: int
) -> HandwritingSubmission:
    db_obj = HandwritingSubmission(
        user_id=owner_id,
        image_url=obj_in.image_url,
        quiz_data=obj_in.quiz_data,
        report_content=obj_in.report_content,
        report_level=obj_in.report_level or 1,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
