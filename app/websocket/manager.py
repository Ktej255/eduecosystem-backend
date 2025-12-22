import socketio
from typing import Dict, Set
import logging
import os

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and rooms for real-time notifications"""

    def __init__(self):
        # Skip Socket.IO server initialization during testing
        if os.getenv("TESTING") == "true":
            self.sio = None
            logger.info("WebSocket manager initialized for testing (Socket.IO disabled)")
        else:
            # Create Socket.IO server
            self.sio = socketio.AsyncServer(
                async_mode="asgi",
                cors_allowed_origins="*",  # Configure properly in production
                logger=True,
                engineio_logger=True,
            )

        # Track active connections: {user_id: set(session_ids)}
        self.active_connections: Dict[int, Set[str]] = {}

    def get_user_room(self, user_id: int) -> str:
        """Get room name for a user"""
        return f"user_{user_id}"

    async def connect(self, sid: str, user_id: int):
        """Handle new connection"""
        try:
            # Join user-specific room
            room = self.get_user_room(user_id)
            await self.sio.enter_room(sid, room)

            # Track connection
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(sid)

            logger.info(f"User {user_id} connected (sid: {sid})")

            # Send connection confirmation
            await self.sio.emit("connected", {"user_id": user_id}, room=sid)

        except Exception as e:
            logger.error(f"Error connecting user {user_id}: {str(e)}")
            raise

    async def disconnect(self, sid: str, user_id: int):
        """Handle disconnection"""
        try:
            # Leave user room
            room = self.get_user_room(user_id)
            await self.sio.leave_room(sid, room)

            # Remove from tracking
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(sid)

                # Clean up if no more connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            logger.info(f"User {user_id} disconnected (sid: {sid})")

        except Exception as e:
            logger.error(f"Error disconnecting user {user_id}: {str(e)}")

    async def send_notification_to_user(self, user_id: int, notification_data: dict):
        """Send notification to a specific user"""
        try:
            room = self.get_user_room(user_id)

            # Emit to all sessions of this user
            await self.sio.emit("new_notification", notification_data, room=room)

            logger.info(f"Sent notification to user {user_id}")

        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {str(e)}")

    async def send_personal_message(self, user_id: int, message: dict):
        """Send personal message to a specific user"""
        try:
            room = self.get_user_room(user_id)
            await self.sio.emit("new_message", message, room=room)
            logger.info(f"Sent message to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {str(e)}")

    # --- WebRTC Signaling ---

    async def handle_join_video_room(self, sid: str, room_id: str, user_id: int):
        """Handle user joining a video room"""
        await self.sio.enter_room(sid, room_id)
        # Notify others in the room
        await self.sio.emit(
            "user_joined", {"user_id": user_id, "sid": sid}, room=room_id, skip_sid=sid
        )
        logger.info(f"User {user_id} joined video room {room_id}")

    async def handle_leave_video_room(self, sid: str, room_id: str, user_id: int):
        """Handle user leaving a video room"""
        await self.sio.leave_room(sid, room_id)
        await self.sio.emit("user_left", {"user_id": user_id, "sid": sid}, room=room_id)
        logger.info(f"User {user_id} left video room {room_id}")

    async def handle_webrtc_offer(self, sid: str, data: dict):
        """Relay WebRTC offer to target peer"""
        target_sid = data.get("target_sid")
        if target_sid:
            await self.sio.emit(
                "offer",
                {
                    "sdp": data["sdp"],
                    "sender_sid": sid,
                    "sender_id": data.get("sender_id"),
                },
                room=target_sid,
            )

    async def handle_webrtc_answer(self, sid: str, data: dict):
        """Relay WebRTC answer to target peer"""
        target_sid = data.get("target_sid")
        if target_sid:
            await self.sio.emit(
                "answer", {"sdp": data["sdp"], "sender_sid": sid}, room=target_sid
            )

    async def handle_ice_candidate(self, sid: str, data: dict):
        """Relay ICE candidate to target peer"""
        target_sid = data.get("target_sid")
        if target_sid:
            await self.sio.emit(
                "ice_candidate",
                {"candidate": data["candidate"], "sender_sid": sid},
                room=target_sid,
            )

    async def broadcast_to_users(self, user_ids: list[int], notification_data: dict):
        """Broadcast notification to multiple users"""
        for user_id in user_ids:
            await self.send_notification_to_user(user_id, notification_data)

    def is_user_connected(self, user_id: int) -> bool:
        """Check if user has any active connections"""
        return (
            user_id in self.active_connections
            and len(self.active_connections[user_id]) > 0
        )

    def get_connected_users_count(self) -> int:
        """Get total number of connected users"""
        return len(self.active_connections)


# Singleton instance
manager = ConnectionManager()
