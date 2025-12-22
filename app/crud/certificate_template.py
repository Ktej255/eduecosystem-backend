from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.certificate_template import CertificateTemplate
from app.schemas import certificate_template as schemas


def create_template(
    db: Session, template: schemas.CertificateTemplateCreate, creator_id: int
) -> CertificateTemplate:
    """Create a new certificate template"""
    db_template = CertificateTemplate(**template.model_dump(), creator_id=creator_id)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


def get_template(db: Session, template_id: int) -> Optional[CertificateTemplate]:
    """Get a certificate template by ID"""
    return (
        db.query(CertificateTemplate)
        .filter(CertificateTemplate.id == template_id)
        .first()
    )


def get_templates(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    public_only: bool = True,
    creator_id: Optional[int] = None,
) -> List[CertificateTemplate]:
    """Get all certificate templates with optional filters"""
    query = db.query(CertificateTemplate)

    if public_only:
        query = query.filter(CertificateTemplate.is_public == True)

    if creator_id:
        query = query.filter(CertificateTemplate.creator_id == creator_id)

    return (
        query.order_by(CertificateTemplate.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_default_template(db: Session) -> Optional[CertificateTemplate]:
    """Get the default certificate template"""
    return (
        db.query(CertificateTemplate)
        .filter(CertificateTemplate.is_default == True)
        .first()
    )


def update_template(
    db: Session, template_id: int, template_update: schemas.CertificateTemplateUpdate
) -> Optional[CertificateTemplate]:
    """Update a certificate template"""
    db_template = get_template(db, template_id)
    if not db_template:
        return None

    update_data = template_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_template, field, value)

    db.commit()
    db.refresh(db_template)
    return db_template


def delete_template(db: Session, template_id: int) -> bool:
    """Delete a certificate template"""
    db_template = get_template(db, template_id)
    if not db_template:
        return False

    # Don't delete if it's the default template
    if db_template.is_default:
        return False

    db.delete(db_template)
    db.commit()
    return True


def set_default_template(
    db: Session, template_id: int
) -> Optional[CertificateTemplate]:
    """Set a template as the default"""
    # Remove default from all templates
    db.query(CertificateTemplate).update({"is_default": False})

    # Set new default
    db_template = get_template(db, template_id)
    if not db_template:
        return None

    db_template.is_default = True
    db.commit()
    db.refresh(db_template)
    return db_template


def get_my_templates(db: Session, creator_id: int) -> List[CertificateTemplate]:
    """Get all templates created by a specific user"""
    return (
        db.query(CertificateTemplate)
        .filter(CertificateTemplate.creator_id == creator_id)
        .order_by(CertificateTemplate.created_at.desc())
        .all()
    )
