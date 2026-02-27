from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.app_config import AppConfig
from app.schemas.app_config import AppConfigCreate, AppConfigUpdate

class CRUDAppConfig(CRUDBase[AppConfig, AppConfigCreate, AppConfigUpdate]):
    def get_by_key(self, db: Session, *, key: str) -> Optional[AppConfig]:
        return db.query(AppConfig).filter(AppConfig.key == key).first()

app_config = CRUDAppConfig(AppConfig)
