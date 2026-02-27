from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app import crud, models, schemas

router = APIRouter()

@router.get("/{key}", response_model=schemas.AppConfig)
def read_app_config(
    key: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch a global dynamic configuration value by key.
    """
    config = crud.app_config.get_by_key(db=db, key=key)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration key not found")
    return config

@router.put("/{key}", response_model=schemas.AppConfig)
def update_app_config(
    key: str,
    config_in: schemas.AppConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update or initialize a configuration key natively in the Postgres Database.
    Restricted to Superuser access.
    """
    config = crud.app_config.get_by_key(db=db, key=key)
    if not config:
        create_data = schemas.AppConfigCreate(
            key=key, 
            value=config_in.value if config_in.value else {}, 
            description=config_in.description
        )
        return crud.app_config.create(db=db, obj_in=create_data)
        
    return crud.app_config.update(db=db, db_obj=config, obj_in=config_in)
