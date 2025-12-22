from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.crud import certificate_template as crud
from app.crud import permissions as crud_permissions
from app.schemas import certificate_template as schemas
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=schemas.CertificateTemplate)
def create_certificate_template(
    template: schemas.CertificateTemplateCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Create a new certificate template.
    Instructors/Admins only.
    """
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "create_certificate_template"
        ):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: create_certificate_template required",
            )

    return crud.create_template(db, template, current_user.id)


@router.get("/", response_model=List[schemas.CertificateTemplate])
def get_certificate_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    public_only: bool = True,
    db: Session = Depends(deps.get_db),
):
    """
    Get all certificate templates.
    """
    return crud.get_templates(db, skip=skip, limit=limit, public_only=public_only)


@router.get("/my-templates", response_model=List[schemas.CertificateTemplate])
def get_my_templates(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get all templates created by the current user.
    """
    return crud.get_my_templates(db, current_user.id)


@router.get("/default", response_model=schemas.CertificateTemplate)
def get_default_template(db: Session = Depends(deps.get_db)):
    """
    Get the default certificate template.
    """
    template = crud.get_default_template(db)
    if not template:
        raise HTTPException(status_code=404, detail="No default template found")
    return template


@router.get("/{template_id}", response_model=schemas.CertificateTemplate)
def get_certificate_template(template_id: int, db: Session = Depends(deps.get_db)):
    """
    Get a specific certificate template by ID.
    """
    template = crud.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/{template_id}", response_model=schemas.CertificateTemplate)
def update_certificate_template(
    template_id: int,
    template_update: schemas.CertificateTemplateUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update a certificate template.
    Creator only.
    """
    db_template = crud.get_template(db, template_id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check permission
    if not current_user.is_superuser:
        if db_template.creator_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Only the creator can update this template"
            )

    updated = crud.update_template(db, template_id, template_update)
    return updated


@router.delete("/{template_id}")
def delete_certificate_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Delete a certificate template.
    Creator only.
    """
    db_template = crud.get_template(db, template_id)
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check permission
    if not current_user.is_superuser:
        if db_template.creator_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Only the creator can delete this template"
            )

    if db_template.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default template")

    crud.delete_template(db, template_id)
    return {"message": "Template deleted successfully"}


@router.post("/{template_id}/set-default", response_model=schemas.CertificateTemplate)
def set_default_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Set a template as the default.
    Admin only.
    """
    # Check admin role
    if not current_user.is_superuser:
        if not crud_permissions.check_role(db, current_user.id, "admin"):
            raise HTTPException(status_code=403, detail="Admin role required")
    template = crud.set_default_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template
