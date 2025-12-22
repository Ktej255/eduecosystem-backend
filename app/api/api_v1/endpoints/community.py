from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from pydantic import BaseModel, ConfigDict

router = APIRouter()


class StudyRoomOut(BaseModel):
    id: int
    name: str
    topic: str
    participants_count: int
    thumbnail_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


@router.get("/rooms", response_model=List[StudyRoomOut])
def get_study_rooms(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get list of active study rooms.
    """
    from app.models.study_room import StudyRoom

    # Mock data if empty
    if db.query(StudyRoom).count() == 0:
        mock_rooms = [
            StudyRoom(
                name="Deep Work Lounge",
                topic="Productivity",
                participants_count=12,
                thumbnail_url="https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=300&q=80",
            ),
            StudyRoom(
                name="Python Learners",
                topic="Coding",
                participants_count=5,
                thumbnail_url="https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=300&q=80",
            ),
            StudyRoom(
                name="Midnight Oil",
                topic="General",
                participants_count=28,
                thumbnail_url="https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=300&q=80",
            ),
        ]
        db.add_all(mock_rooms)
        db.commit()

    return db.query(StudyRoom).all()


@router.post("/rooms/join")
def join_room(
    room_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Join a study room (increments count).
    """
    from app.models.study_room import StudyRoom

    room = db.query(StudyRoom).filter(StudyRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room.participants_count += 1
    db.commit()

    return {"msg": "Joined room", "room": room.name}
