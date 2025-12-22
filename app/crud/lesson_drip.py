from typing import Optional
from sqlalchemy.orm import Session
from app.models.lesson_drip import LessonDripSetting
from app.schemas.lesson_drip import DripSettingCreate, DripSettingUpdate


class CRUDLessonDrip:
    def get(self, db: Session, drip_id: int) -> Optional[LessonDripSetting]:
        """Get drip setting by ID"""
        return (
            db.query(LessonDripSetting).filter(LessonDripSetting.id == drip_id).first()
        )

    def get_by_lesson(self, db: Session, lesson_id: int) -> Optional[LessonDripSetting]:
        """Get active drip setting for a lesson"""
        return (
            db.query(LessonDripSetting)
            .filter(
                LessonDripSetting.lesson_id == lesson_id,
                LessonDripSetting.is_active == True,
            )
            .first()
        )

    def create(self, db: Session, obj_in: DripSettingCreate) -> LessonDripSetting:
        """Create new drip setting"""
        drip_setting = LessonDripSetting(**obj_in.model_dump())
        db.add(drip_setting)
        db.commit()
        db.refresh(drip_setting)
        return drip_setting

    def update(
        self, db: Session, drip_id: int, obj_in: DripSettingUpdate
    ) -> LessonDripSetting:
        """Update existing drip setting"""
        drip_setting = self.get(db, drip_id)
        if not drip_setting:
            return None

        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(drip_setting, field, value)

        db.commit()
        db.refresh(drip_setting)
        return drip_setting

    def delete(self, db: Session, drip_id: int) -> bool:
        """Delete drip setting"""
        drip_setting = self.get(db, drip_id)
        if not drip_setting:
            return False

        db.delete(drip_setting)
        db.commit()
        return True


lesson_drip = CRUDLessonDrip()
