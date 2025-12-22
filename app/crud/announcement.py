from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.announcement import CourseAnnouncement, AnnouncementRead
from app.models.enrollment import Enrollment
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate


class CRUDAnnouncement(
    CRUDBase[CourseAnnouncement, AnnouncementCreate, AnnouncementUpdate]
):
    def get_by_course(
        self,
        db: Session,
        *,
        course_id: int,
        skip: int = 0,
        limit: int = 20,
        include_unpublished: bool = False,
    ) -> List[CourseAnnouncement]:
        """Get announcements for a course"""
        query = db.query(CourseAnnouncement).filter(
            CourseAnnouncement.course_id == course_id
        )

        if not include_unpublished:
            query = query.filter(CourseAnnouncement.is_published == True)

        return (
            query.order_by(
                desc(CourseAnnouncement.is_pinned), desc(CourseAnnouncement.created_at)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_instructor(
        self, db: Session, *, obj_in: AnnouncementCreate, instructor_id: int
    ) -> CourseAnnouncement:
        """Create a new announcement"""
        obj_data = obj_in.model_dump()
        obj_data["instructor_id"] = instructor_id

        if obj_in.is_published:
            obj_data["published_at"] = datetime.utcnow()

        db_obj = CourseAnnouncement(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Send notifications if enabled
        if obj_in.send_notification and obj_in.is_published:
            self._send_notifications(db, announcement=db_obj)

        return db_obj

    def _send_notifications(
        self, db: Session, *, announcement: CourseAnnouncement
    ) -> None:
        """Send notifications to all enrolled students"""
        from app.services.notification_helpers import create_and_emit_notification
        from app.models.notification import NotificationType

        # Get all enrolled students
        enrollments = (
            db.query(Enrollment)
            .filter(
                Enrollment.course_id == announcement.course_id,
                Enrollment.status == "active",
            )
            .all()
        )

        # Create notification for each student
        for enrollment in enrollments:
            if (
                enrollment.user_id != announcement.instructor_id
            ):  # Don't notify instructor
                create_and_emit_notification(
                    db=db,
                    user_id=enrollment.user_id,
                    notification_type=NotificationType.COURSE_ANNOUNCEMENT,
                    title=f"New announcement: {announcement.title}",
                    message=announcement.content[:200],  # Preview
                    data={
                        "course_id": announcement.course_id,
                        "announcement_id": announcement.id,
                    },
                    action_url=f"/lms/courses/{announcement.course_id}/announcements/{announcement.id}",
                )

    def mark_as_read(
        self, db: Session, *, announcement_id: int, user_id: int
    ) -> AnnouncementRead:
        """Mark announcement as read by user"""
        # Check if already read
        existing = (
            db.query(AnnouncementRead)
            .filter(
                AnnouncementRead.announcement_id == announcement_id,
                AnnouncementRead.user_id == user_id,
            )
            .first()
        )

        if existing:
            return existing

        # Create read record
        read_record = AnnouncementRead(announcement_id=announcement_id, user_id=user_id)
        db.add(read_record)
        db.commit()
        db.refresh(read_record)
        return read_record

    def is_read_by_user(
        self, db: Session, *, announcement_id: int, user_id: int
    ) -> bool:
        """Check if user has read announcement"""
        return (
            db.query(AnnouncementRead)
            .filter(
                AnnouncementRead.announcement_id == announcement_id,
                AnnouncementRead.user_id == user_id,
            )
            .first()
            is not None
        )

    def get_unread_count(self, db: Session, *, course_id: int, user_id: int) -> int:
        """Get count of unread announcements for user in course"""
        all_announcements = self.get_by_course(db, course_id=course_id, limit=1000)

        unread_count = 0
        for announcement in all_announcements:
            if not self.is_read_by_user(
                db, announcement_id=announcement.id, user_id=user_id
            ):
                unread_count += 1

        return unread_count


# Create instance
announcement = CRUDAnnouncement(CourseAnnouncement)
