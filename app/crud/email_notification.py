"""
CRUD operations for Email Notification System
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.email_notification import UserEmailPreference, EmailTemplate, EmailLog
from app.schemas.notification import (
    EmailPreferenceUpdate,
    EmailTemplateCreate,
    EmailTemplateUpdate,
)


class CRUDEmailPreference:
    """CRUD operations for user email preferences"""

    def get(self, db: Session, user_id: int) -> Optional[UserEmailPreference]:
        """Get user's email preferences"""
        return (
            db.query(UserEmailPreference)
            .filter(UserEmailPreference.user_id == user_id)
            .first()
        )

    def create_default(self, db: Session, user_id: int) -> UserEmailPreference:
        """Create default email preferences for a user"""
        preferences = UserEmailPreference(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
        return preferences

    def get_or_create(self, db: Session, user_id: int) -> UserEmailPreference:
        """Get existing preferences or create default ones"""
        preferences = self.get(db, user_id)
        if not preferences:
            preferences = self.create_default(db, user_id)
        return preferences

    def update(
        self, db: Session, user_id: int, obj_in: EmailPreferenceUpdate
    ) -> UserEmailPreference:
        """Update user's email preferences"""
        preferences = self.get_or_create(db, user_id)

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)

        db.add(preferences)
        db.commit()
        db.refresh(preferences)
        return preferences

    def reset_to_default(self, db: Session, user_id: int) -> UserEmailPreference:
        """Reset user preferences to defaults"""
        preferences = self.get_or_create(db, user_id)

        # Reset all to True (default state)
        preferences.enrollment_enabled = True
        preferences.assignment_enabled = True
        preferences.quiz_enabled = True
        preferences.certificate_enabled = True
        preferences.announcement_enabled = True
        preferences.review_enabled = True
        preferences.course_update_enabled = True
        preferences.general_enabled = True
        preferences.all_emails_enabled = True

        db.add(preferences)
        db.commit()
        db.refresh(preferences)
        return preferences


class CRUDEmailTemplate:
    """CRUD operations for email templates"""

    def get(self, db: Session, template_id: int) -> Optional[EmailTemplate]:
        """Get template by ID"""
        return db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[EmailTemplate]:
        """Get template by name"""
        return db.query(EmailTemplate).filter(EmailTemplate.name == name).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        include_system: bool = True,
    ) -> List[EmailTemplate]:
        """Get multiple templates"""
        query = db.query(EmailTemplate)

        if not include_system:
            query = query.filter(EmailTemplate.is_system == False)

        if user_id:
            query = query.filter(EmailTemplate.created_by == user_id)

        return query.offset(skip).limit(limit).all()

    def create(
        self, db: Session, obj_in: EmailTemplateCreate, created_by: Optional[int] = None
    ) -> EmailTemplate:
        """Create new email template"""
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.dict()
            
        template = EmailTemplate(
            **obj_in_data, created_by=created_by, is_system=False
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def update(
        self, db: Session, template_id: int, obj_in: EmailTemplateUpdate
    ) -> Optional[EmailTemplate]:
        """Update email template"""
        template = self.get(db, template_id)
        if not template or template.is_system:
            return None

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def delete(self, db: Session, template_id: int) -> bool:
        """Delete email template (only custom templates, not system)"""
        template = self.get(db, template_id)
        if not template or template.is_system:
            return False

        db.delete(template)
        db.commit()
        return True


class CRUDEmailLog:
    """CRUD operations for email logs"""

    def get(self, db: Session, log_id: int) -> Optional[EmailLog]:
        """Get email log by ID"""
        return db.query(EmailLog).filter(EmailLog.id == log_id).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[EmailLog]:
        """Get multiple email logs"""
        query = db.query(EmailLog)

        if user_id:
            query = query.filter(EmailLog.user_id == user_id)

        if status:
            query = query.filter(EmailLog.status == status)

        return (
            query.order_by(EmailLog.created_at.desc()).offset(skip).limit(limit).all()
        )

    def get_count(self, db: Session, user_id: Optional[int] = None) -> int:
        """Get total count of email logs"""
        query = db.query(EmailLog)
        if user_id:
            query = query.filter(EmailLog.user_id == user_id)
        return query.count()


# Create instances
crud_email_preference = CRUDEmailPreference()
crud_email_template = CRUDEmailTemplate()
crud_email_log = CRUDEmailLog()
