"""
Real-Time Service Layer
Handles real-time broadcasting of notifications, messages, and updates via WebSocket
"""

from typing import Dict, List
from sqlalchemy.orm import Session
from app.core.websocket import manager
from app.models.notification import Notification, NotificationType, NotificationPriority
from datetime import datetime


class RealtimeService:
    """Service for real-time operations"""

    @staticmethod
    async def send_notification_realtime(
        db: Session, user_id: int, notification: Notification
    ) -> bool:
        """
        Send notification via WebSocket to user

        Args:
            db: Database session
            user_id: Target user ID
            notification: Notification object

        Returns:
            True if delivered via WebSocket, False otherwise
        """
        try:
            # Prepare notification payload
            notification_data = {
                "type": "notification",
                "notification": {
                    "id": notification.id,
                    "type": notification.type.value
                    if hasattr(notification.type, "value")
                    else notification.type,
                    "title": notification.title,
                    "message": notification.message,
                    "data": notification.data,
                    "action_url": notification.action_url,
                    "priority": notification.priority.value
                    if hasattr(notification.priority, "value")
                    else notification.priority,
                    "created_at": notification.created_at.isoformat(),
                    "is_read": notification.is_read,
                },
            }

            # Broadcast to all user connections
            await manager.broadcast_to_user(user_id, notification_data)

            # Mark as delivered via real-time
            notification.mark_delivered_realtime()
            db.commit()

            return True
        except Exception as e:
            print(f"Error sending real-time notification: {e}")
            return False

    @staticmethod
    async def send_chat_message(
        room: str, message: Dict, exclude_websocket=None
    ) -> bool:
        """
        Broadcast chat message to room

        Args:
            room: Room ID (e.g., "discussion:123", "course:456")
            message: Message data
            exclude_websocket: WebSocket to exclude from broadcast

        Returns:
            True if sent successfully
        """
        try:
            await manager.broadcast_to_room(
                room, {"type": "chat_message", **message}, exclude=exclude_websocket
            )
            return True
        except Exception as e:
            print(f"Error broadcasting chat message: {e}")
            return False

    @staticmethod
    async def send_live_class_update(
        class_id: int, update_type: str, data: Dict
    ) -> bool:
        """
        Send live class update to all participants

        Args:
            class_id: Live class ID
            update_type: Type of update (started, ended, poll_created, etc.)
            data: Update data

        Returns:
            True if sent successfully
        """
        try:
            room = f"live_class:{class_id}"
            await manager.broadcast_to_room(
                room,
                {
                    "type": "live_class_update",
                    "update_type": update_type,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            return True
        except Exception as e:
            print(f"Error sending live class update: {e}")
            return False

    @staticmethod
    async def send_presence_update(
        room: str,
        user_id: int,
        user_name: str,
        status: str,  # online, offline, away
    ) -> bool:
        """
        Broadcast user presence status to room

        Args:
            room: Room ID
            user_id: User ID
            user_name: User name
            status: Presence status

        Returns:
            True if sent successfully
        """
        try:
            # Use batching for presence updates as they can be frequent
            await manager.broadcast_to_room(
                room,
                {
                    "type": "presence_update",
                    "user_id": user_id,
                    "user_name": user_name,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                batch=True,
            )
            return True
        except Exception as e:
            print(f"Error sending presence update: {e}")
            return False

    @staticmethod
    async def send_reaction(room: str, reaction: str, user_id: int) -> bool:
        """
        Broadcast reaction to room (batched)
        """
        try:
            await manager.broadcast_to_room(
                room,
                {"type": "reaction", "reaction": reaction, "user_id": user_id},
                batch=True,
            )
            return True
        except Exception as e:
            print(f"Error sending reaction: {e}")
            return False

    @staticmethod
    async def send_quiz_update(
        quiz_session_id: int, update_type: str, data: Dict
    ) -> bool:
        """
        Send quiz session update (leaderboard, question change, etc.)

        Args:
            quiz_session_id: Quiz session ID
            update_type: Type of update
            data: Update data

        Returns:
            True if sent successfully
        """
        try:
            room = f"quiz:{quiz_session_id}"
            await manager.broadcast_to_room(
                room,
                {
                    "type": "quiz_update",
                    "update_type": update_type,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            return True
        except Exception as e:
            print(f"Error sending quiz update: {e}")
            return False

    @staticmethod
    async def notify_assignment_graded(
        db: Session,
        student_id: int,
        assignment_title: str,
        grade: float,
        assignment_id: int,
    ):
        """
        Create and send real-time notification for graded assignment

        Args:
            db: Database session
            student_id: Student user ID
            assignment_title: Assignment title
            grade: Grade received
            assignment_id: Assignment ID
        """
        notification = Notification(
            user_id=student_id,
            type=NotificationType.ASSIGNMENT_GRADED,
            title="Assignment Graded",
            message=f"Your assignment '{assignment_title}' has been graded. Score: {grade}%",
            data={"assignment_id": assignment_id, "grade": grade},
            action_url=f"/lms/assignments/{assignment_id}",
            priority=NotificationPriority.HIGH,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Send via WebSocket
        await RealtimeService.send_notification_realtime(db, student_id, notification)

    @staticmethod
    async def notify_live_class_starting(
        db: Session,
        enrolled_student_ids: List[int],
        class_title: str,
        class_id: int,
        start_time: datetime,
    ):
        """
        Notify all enrolled students that live class is starting

        Args:
            db: Database session
            enrolled_student_ids: List of enrolled student IDs
            class_title: Live class title
            class_id: Live class ID
            start_time: Start time
        """
        for student_id in enrolled_student_ids:
            notification = Notification(
                user_id=student_id,
                type=NotificationType.LIVE_CLASS_STARTING,
                title="Live Class Starting Soon",
                message=f"'{class_title}' is starting in 5 minutes",
                data={"live_class_id": class_id, "start_time": start_time.isoformat()},
                action_url=f"/lms/live-classes/{class_id}",
                priority=NotificationPriority.URGENT,
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)

            # Send via WebSocket
            await RealtimeService.send_notification_realtime(
                db, student_id, notification
            )

    @staticmethod
    def get_online_users_count(room: str) -> int:
        """Get count of online users in a room"""
        return manager.get_room_count(room)


# Create global instance
realtime_service = RealtimeService()
