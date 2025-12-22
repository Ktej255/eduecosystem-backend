from typing import List
from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def get_multi_by_owner(
    db: Session, *, user_id: int, skip: int = 0, limit: int = 100
) -> List[Task]:
    return (
        db.query(Task).filter(Task.user_id == user_id).offset(skip).limit(limit).all()
    )


def create_with_owner(db: Session, *, obj_in: TaskCreate, user_id: int) -> Task:
    db_obj = Task(
        title=obj_in.title,
        description=obj_in.description,
        task_type=obj_in.task_type,
        duration_minutes=obj_in.duration_minutes,
        scheduled_date=obj_in.scheduled_date,
        is_master=obj_in.is_master,
        user_id=user_id,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, *, db_obj: Task, obj_in: TaskUpdate) -> Task:
    update_data = obj_in.dict(exclude_unset=True)
    for field in update_data:
        setattr(db_obj, field, update_data[field])
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
