"""
Email Notification API Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.crud.email_notification import (
    crud_email_preference,
    crud_email_template,
    crud_email_log,
)
from app.schemas.notification import (
    EmailPreference,
    EmailPreferenceUpdate,
    EmailTemplate,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailLog,
)

router = APIRouter()


# =============================================================================
# EMAIL PREFERENCES ENDPOINTS
# =============================================================================


@router.get("/preferences", response_model=EmailPreference)
def get_email_preferences(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get current user's email notification preferences"""
    preferences = crud_email_preference.get_or_create(db, user_id=current_user.id)
    return preferences


@router.patch("/preferences", response_model=EmailPreference)
def update_email_preferences(
    preferences_in: EmailPreferenceUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Update current user's email notification preferences"""
    preferences = crud_email_preference.update(
        db, user_id=current_user.id, obj_in=preferences_in
    )
    return preferences


@router.put("/preferences/reset", response_model=EmailPreference)
def reset_email_preferences(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Reset email preferences to default values"""
    preferences = crud_email_preference.reset_to_default(db, user_id=current_user.id)
    return preferences


# =============================================================================
# EMAIL TEMPLATES ENDPOINTS
# =============================================================================


@router.get("/templates", response_model=List[EmailTemplate])
def get_email_templates(
    skip: int = 0,
    limit: int = 100,
    include_system: bool = True,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get email templates (system + user's custom templates)"""
    # Get all system templates
    templates = crud_email_template.get_multi(
        db, skip=skip, limit=limit, include_system=include_system
    )

    # Filter to show only system templates or user's own custom templates
    if not current_user.is_superuser:
        templates = [
            t for t in templates if t.is_system or t.created_by == current_user.id
        ]

    return templates


@router.get("/templates/{template_id}", response_model=EmailTemplate)
def get_email_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get a specific email template"""
    template = crud_email_template.get(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check permissions
    if (
        not template.is_system
        and template.created_by != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to view this template"
        )

    return template


@router.post(
    "/templates", response_model=EmailTemplate, status_code=status.HTTP_201_CREATED
)
def create_email_template(
    template_in: EmailTemplateCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Create a custom email template"""
    # Check if template name already exists
    existing = crud_email_template.get_by_name(db, name=template_in.name)
    if existing:
        raise HTTPException(
            status_code=400, detail="Template with this name already exists"
        )

    template = crud_email_template.create(
        db, obj_in=template_in, created_by=current_user.id
    )
    return template


@router.patch("/templates/{template_id}", response_model=EmailTemplate)
def update_email_template(
    template_id: int,
    template_in: EmailTemplateUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Update a custom email template"""
    template = crud_email_template.get(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check permissions
    if template.is_system:
        raise HTTPException(status_code=403, detail="Cannot modify system templates")

    if template.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this template"
        )

    template = crud_email_template.update(
        db, template_id=template_id, obj_in=template_in
    )
    if not template:
        raise HTTPException(status_code=400, detail="Failed to update template")

    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Delete a custom email template"""
    template = crud_email_template.get(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check permissions
    if template.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system templates")

    if template.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this template"
        )

    success = crud_email_template.delete(db, template_id=template_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete template")


# =============================================================================
# EMAIL LOGS ENDPOINTS (Admin only)
# =============================================================================


@router.get("/logs", response_model=List[EmailLog])
def get_email_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: int = None,
    status_filter: str = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get email logs (admin only)"""
    if not current_user.is_superuser:
        # Non-admins can only see their own logs
        user_id = current_user.id

    logs = crud_email_log.get_multi(
        db, skip=skip, limit=limit, user_id=user_id, status=status_filter
    )
    return logs


@router.get("/logs/{log_id}", response_model=EmailLog)
def get_email_log(
    log_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get a specific email log"""
    log = crud_email_log.get(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Email log not found")

    # Check permissions
    if log.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to view this log")

    return log
