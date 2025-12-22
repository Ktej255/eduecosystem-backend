"""
Presence service for tracking user online/offline/away status.
"""

from sqlalchemy.orm import Session
from app.models.chat import RealtimeUserPresence
from datetime import datetime, timedelta
from typing import List, Optional
from app.core.cache import cache


class PresenceService:
    """Service for managing user presence."""

    @staticmethod
    def update_presence(
        db: Session,
        user_id: int,
        status: str,
        status_message: Optional[str] = None,
        current_location: Optional[str] = None,
    ) -> RealtimeUserPresence:
        """
        Update user presence status.

        Args:
            db: Database session
            user_id: User ID
            status: Presence status (online, offline, away, busy)
            status_message: Custom status message
            current_location: Current location in app

        Returns:
            Updated RealtimeUserPresence object
        """
        presence = (
            db.query(RealtimeUserPresence)
            .filter(RealtimeUserPresence.user_id == user_id)
            .first()
        )

        if not presence:
            presence = RealtimeUserPresence(user_id=user_id)
            db.add(presence)

        presence.status = status
        presence.last_activity = datetime.utcnow()

        if status == "online":
            presence.last_seen = datetime.utcnow()

        if status_message is not None:
            presence.status_message = status_message

        if current_location is not None:
            presence.current_location = current_location

        db.commit()
        db.refresh(presence)

        # Cache the presence status
        cache.set(
            f"presence:{user_id}",
            {
                "status": status,
                "last_seen": presence.last_seen.isoformat(),
                "current_location": current_location,
            },
            ttl=300,
        )  # 5 minutes

        return presence

    @staticmethod
    def get_presence(db: Session, user_id: int) -> Optional[RealtimeUserPresence]:
        """
        Get user presence status.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            RealtimeUserPresence object or None
        """
        # Try cache first
        cached = cache.get(f"presence:{user_id}")
        if cached:
            presence = (
                db.query(RealtimeUserPresence)
                .filter(RealtimeUserPresence.user_id == user_id)
                .first()
            )
            return presence

        presence = (
            db.query(RealtimeUserPresence)
            .filter(RealtimeUserPresence.user_id == user_id)
            .first()
        )

        if presence:
            # Cache for next time
            cache.set(
                f"presence:{user_id}",
                {
                    "status": presence.status,
                    "last_seen": presence.last_seen.isoformat()
                    if presence.last_seen
                    else None,
                    "current_location": presence.current_location,
                },
                ttl=300,
            )

        return presence

    @staticmethod
    def get_online_users(
        db: Session, location: Optional[str] = None
    ) -> List[RealtimeUserPresence]:
        """
        Get list of currently online users.

        Args:
            db: Database session
            location: Optional filter by current location

        Returns:
            List of RealtimeUserPresence objects
        """
        query = db.query(RealtimeUserPresence).filter(
            RealtimeUserPresence.status == "online"
        )

        if location:
            query = query.filter(RealtimeUserPresence.current_location == location)

        # Consider users active if seen within last 5 minutes
        active_threshold = datetime.utcnow() - timedelta(minutes=5)
        query = query.filter(RealtimeUserPresence.last_activity >= active_threshold)

        return query.all()

    @staticmethod
    def set_offline(db: Session, user_id: int):
        """
        Set user as offline.

        Args:
            db: Database session
            user_id: User ID
        """
        presence = (
            db.query(RealtimeUserPresence)
            .filter(RealtimeUserPresence.user_id == user_id)
            .first()
        )

        if presence:
            presence.status = "offline"
            presence.last_seen = datetime.utcnow()
            db.commit()

            # Update cache
            cache.set(
                f"presence:{user_id}",
                {
                    "status": "offline",
                    "last_seen": presence.last_seen.isoformat(),
                    "current_location": presence.current_location,
                },
                ttl=300,
            )

    @staticmethod
    def heartbeat(db: Session, user_id: int):
        """
        Update last activity timestamp (heartbeat).

        Args:
            db: Database session
            user_id: User ID
        """
        presence = (
            db.query(RealtimeUserPresence)
            .filter(RealtimeUserPresence.user_id == user_id)
            .first()
        )

        if presence:
            presence.last_activity = datetime.utcnow()

            # If user was away, set them back to online
            if presence.status in ["away", "offline"]:
                presence.status = "online"
                presence.last_seen = datetime.utcnow()

            db.commit()

            # Update cache
            cache.set(
                f"presence:{user_id}",
                {
                    "status": presence.status,
                    "last_seen": presence.last_seen.isoformat(),
                    "current_location": presence.current_location,
                },
                ttl=300,
            )

    @staticmethod
    def cleanup_stale_presence(db: Session, threshold_minutes: int = 15):
        """
        Mark users as offline if they haven't been active recently.

        Args:
            db: Database session
            threshold_minutes: Minutes of inactivity before marking offline
        """
        threshold = datetime.utcnow() - timedelta(minutes=threshold_minutes)

        stale_presence = (
            db.query(RealtimeUserPresence)
            .filter(
                RealtimeUserPresence.status.in_(["online", "away"]),
                RealtimeUserPresence.last_activity < threshold,
            )
            .all()
        )

        for presence in stale_presence:
            presence.status = "offline"
            presence.last_seen = presence.last_activity
            cache.delete(f"presence:{presence.user_id}")

        db.commit()

        return len(stale_presence)


presence_service = PresenceService()
