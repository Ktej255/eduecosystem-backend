from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.meditation import MeditationSession
from app.schemas.meditation import MeditationSessionCreate


def create_with_owner(
    db: Session, *, obj_in: MeditationSessionCreate, user_id: int
) -> MeditationSession:
    db_obj = MeditationSession(
        user_id=user_id, minutes_listened=obj_in.minutes_listened
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_total_minutes(db: Session, *, user_id: int) -> int:
    result = (
        db.query(func.sum(MeditationSession.minutes_listened))
        .filter(MeditationSession.user_id == user_id)
        .scalar()
    )
    return result or 0
