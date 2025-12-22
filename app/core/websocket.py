"""
WebSocket Server for Real-Time Features
Handles WebSocket connections for live discussions, quizzes, and notifications
"""

from fastapi import WebSocket
from typing import Dict, Set, Optional
import asyncio
from datetime import datetime
from app.core.cache import cache
from app.services.presence import presence_service
from app.db.session import SessionLocal


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        # Store active connections by room
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map WebSocket to user info
        self.connection_users: Dict[WebSocket, dict] = {}

    async def connect(
        self, websocket: WebSocket, room: str, user_id: int, user_name: str
    ):
        """Accept WebSocket connection and add to room"""
        await websocket.accept()

        if room not in self.active_connections:
            self.active_connections[room] = set()

        self.active_connections[room].add(websocket)
        self.connection_users[websocket] = {
            "user_id": user_id,
            "user_name": user_name,
            "room": room,
            "connected_at": datetime.utcnow().isoformat(),
        }

        # Notify room about new user
        await self.broadcast_to_room(
            room,
            {
                "type": "user_joined",
                "user_id": user_id,
                "user_name": user_name,
                "timestamp": datetime.utcnow().isoformat(),
            },
            exclude=websocket,
        )

        # Update presence to online
        try:
            db = SessionLocal()
            presence_service.update_presence(
                db=db, user_id=user_id, status="online", current_location=f"room:{room}"
            )
            db.close()
        except Exception as e:
            print(f"Error updating presence: {e}")

        # Send current online users to new connection
        online_users = await self.get_online_users(room)
        await websocket.send_json({"type": "online_users", "users": online_users})

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.connection_users:
            user_info = self.connection_users[websocket]
            room = user_info["room"]

            if room in self.active_connections:
                self.active_connections[room].discard(websocket)

                if not self.active_connections[room]:
                    del self.active_connections[room]

            del self.connection_users[websocket]

            # Notify room about user leaving
            asyncio.create_task(
                self.broadcast_to_room(
                    room,
                    {
                        "type": "user_left",
                        "user_id": user_info["user_id"],
                        "user_name": user_info["user_name"],
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            )

            # Set user offline
            try:
                db = SessionLocal()
                presence_service.set_offline(db=db, user_id=user_info["user_id"])
                db.close()
            except Exception as e:
                print(f"Error setting offline: {e}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        await websocket.send_json(message)

    async def broadcast_to_room(
        self, room: str, message: dict, exclude: Optional[WebSocket] = None
    ):
        """Broadcast message to all connections in a room"""
        if room not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[room]:
            if connection == exclude:
                continue

            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_to_user(self, user_id: int, message: dict):
        """Send message to all connections of a specific user"""
        for websocket, user_info in self.connection_users.items():
            if user_info["user_id"] == user_id:
                try:
                    await websocket.send_json(message)
                except Exception:
                    self.disconnect(websocket)

    async def get_online_users(self, room: str) -> list:
        """Get list of online users in a room"""
        if room not in self.active_connections:
            return []

        online_users = []
        seen_users = set()

        for websocket in self.active_connections[room]:
            user_info = self.connection_users.get(websocket)
            if user_info and user_info["user_id"] not in seen_users:
                online_users.append(
                    {
                        "user_id": user_info["user_id"],
                        "user_name": user_info["user_name"],
                    }
                )
                seen_users.add(user_info["user_id"])

        return online_users

    def get_room_count(self, room: str) -> int:
        """Get number of connections in a room"""
        return len(self.active_connections.get(room, set()))


# Global connection manager
manager = ConnectionManager()


class TypingIndicator:
    """Manage typing indicators for real-time discussions"""

    def __init__(self):
        self.prefix = "typing"

    async def set_typing(self, room: str, user_id: int, user_name: str):
        """Mark user as typing"""
        if not cache.is_available():
            return

        key = f"{self.prefix}:{room}:{user_id}"
        if cache.client:
            cache.client.setex(key, 5, user_name)  # Expire after 5 seconds

        # Broadcast typing status
        await manager.broadcast_to_room(
            room, {"type": "user_typing", "user_id": user_id, "user_name": user_name}
        )

    async def stop_typing(self, room: str, user_id: int):
        """Mark user as stopped typing"""
        if not cache.is_available():
            return

        key = f"{self.prefix}:{room}:{user_id}"
        if cache.client:
            cache.client.delete(key)

        await manager.broadcast_to_room(
            room, {"type": "user_stopped_typing", "user_id": user_id}
        )

    def get_typing_users(self, room: str) -> list:
        """Get list of users currently typing in room"""
        if not cache.is_available() or not cache.client:
            return []

        pattern = f"{self.prefix}:{room}:*"
        typing_users = []

        for key in cache.client.scan_iter(match=pattern):
            user_name = cache.client.get(key)
            if user_name:
                user_id = int(key.split(":")[-1])
                typing_users.append({"user_id": user_id, "user_name": user_name})

        return typing_users


typing_indicator = TypingIndicator()
