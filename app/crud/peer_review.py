from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.crud.base import CRUDBase
from app.models.peer_review import PeerReview, PeerReviewAssignment, PeerReviewStatus
from app.schemas.peer_review import (
    PeerReviewCreate,
    PeerReviewUpdate,
    PeerReviewAssignmentCreate,
    PeerReviewAssignmentUpdate,
)


class CRUDPeerReviewAssignment(
    CRUDBase[
        PeerReviewAssignment, PeerReviewAssignmentCreate, PeerReviewAssignmentUpdate
    ]
):
    def get_by_reviewer(
        self, db: Session, *, reviewer_id: int, skip: int = 0, limit: int = 100
    ) -> List[PeerReviewAssignment]:
        """Get reviews assigned to a student (to give)"""
        return (
            db.query(PeerReviewAssignment)
            .filter(PeerReviewAssignment.reviewer_id == reviewer_id)
            .order_by(desc(PeerReviewAssignment.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_reviewee(
        self, db: Session, *, reviewee_id: int, skip: int = 0, limit: int = 100
    ) -> List[PeerReviewAssignment]:
        """Get reviews received by a student"""
        return (
            db.query(PeerReviewAssignment)
            .filter(PeerReviewAssignment.reviewee_id == reviewee_id)
            .order_by(desc(PeerReviewAssignment.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_assignment(
        self, db: Session, *, assignment_id: int, skip: int = 0, limit: int = 100
    ) -> List[PeerReviewAssignment]:
        """Get all peer review assignments for a specific course assignment"""
        return (
            db.query(PeerReviewAssignment)
            .filter(PeerReviewAssignment.assignment_id == assignment_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(
        self, db: Session, *, obj_in: PeerReviewAssignmentCreate
    ) -> PeerReviewAssignment:
        """Override create to ensure SQLite-compatible naive datetimes"""
        obj_in_data = obj_in.model_dump()

        # Strip timezone from due_date for SQLite compatibility
        if obj_in_data.get("due_date") and obj_in_data["due_date"].tzinfo is not None:
            obj_in_data["due_date"] = obj_in_data["due_date"].replace(tzinfo=None)

        db_obj = PeerReviewAssignment(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CRUDPeerReview(CRUDBase[PeerReview, PeerReviewCreate, PeerReviewUpdate]):
    def create_with_assignment(
        self, db: Session, *, obj_in: PeerReviewCreate
    ) -> PeerReview:
        """Create a review and update the assignment status"""
        db_obj = PeerReview(**obj_in.model_dump())
        db.add(db_obj)

        # Update assignment status
        assignment = (
            db.query(PeerReviewAssignment)
            .filter(PeerReviewAssignment.id == obj_in.peer_review_assignment_id)
            .first()
        )
        if assignment:
            assignment.status = PeerReviewStatus.SUBMITTED

        db.commit()
        db.refresh(db_obj)
        return db_obj


peer_review_assignment = CRUDPeerReviewAssignment(PeerReviewAssignment)
peer_review = CRUDPeerReview(PeerReview)
