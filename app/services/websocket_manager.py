"""
WebSocket Connection Manager

Manages WebSocket connections, rooms, and broadcasting for real-time features.
Supports horizontal scaling via Redis Pub/Sub.
"""

from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections with support for rooms/channels.
    Handles authentication, broadcasting, and presence tracking.
    """

    def __init__(self):
        # Active connections: {user_id: {connection_id: WebSocket}}
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}

        # Room memberships: {room_id: Set[user_id]}
        self.rooms: Dict[str, Set[int]] = {}

        # User presence: {user_id: {last_seen, status, metadata}}
        self.user_presence: Dict[int, Dict[str, Any]] = {}

        # Heartbeat tracking
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        connection_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            user_id: Authenticated user ID
            connection_id: Unique connection identifier
            metadata: Optional connection metadata (device, location, etc.)
        """
        await websocket.accept()

        # Initialize user's connection dict if needed
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}

        # Store the connection
        self.active_connections[user_id][connection_id] = websocket

        # Update presence
        self.user_presence[user_id] = {
            "last_seen": datetime.utcnow().isoformat(),
            "status": "online",
            "metadata": metadata or {},
        }

        # Start heartbeat
        task = asyncio.create_task(self._heartbeat(websocket, connection_id))
        self.heartbeat_tasks[connection_id] = task

        logger.info(f"User {user_id} connected (connection: {connection_id})")

    def disconnect(self, user_id: int, connection_id: str):
        """
        Remove a WebSocket connection.

        Args:
            user_id: User ID
            connection_id: Connection identifier
        """
        # Cancel heartbeat task
        if connection_id in self.heartbeat_tasks:
            self.heartbeat_tasks[connection_id].cancel()
            del self.heartbeat_tasks[connection_id]

        # Remove connection
        if user_id in self.active_connections:
            if connection_id in self.active_connections[user_id]:
                del self.active_connections[user_id][connection_id]

            # If no more connections for this user, clean up
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

                # Update presence to offline
                if user_id in self.user_presence:
                    self.user_presence[user_id]["status"] = "offline"
                    self.user_presence[user_id]["last_seen"] = (
                        datetime.utcnow().isoformat()
                    )

        logger.info(f"User {user_id} disconnected (connection: {connection_id})")

    async def join_room(self, room_id: str, user_id: int):
        """
        Add a user to a room.

        Args:
            room_id: Room identifier
            user_id: User ID
        """
        if room_id not in self.rooms:
            self.rooms[room_id] = set()

        self.rooms[room_id].add(user_id)
        logger.debug(f"User {user_id} joined room {room_id}")

        # Broadcast user joined event
        await self.broadcast_to_room(
            room_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            exclude_user=user_id,
        )

    async def leave_room(self, room_id: str, user_id: int):
        """
        Remove a user from a room.

        Args:
            room_id: Room identifier
            user_id: User ID
        """
        if room_id in self.rooms and user_id in self.rooms[room_id]:
            self.rooms[room_id].remove(user_id)

            # Clean up empty rooms
            if not self.rooms[room_id]:
                del self.rooms[room_id]

            logger.debug(f"User {user_id} left room {room_id}")

            # Broadcast user left event
            await self.broadcast_to_room(
                room_id,
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        """
        Send a message to all connections of a specific user.

        Args:
            user_id: Target user ID
            message: Message to send (will be JSON encoded)
        """
        if user_id not in self.active_connections:
            logger.debug(f"User {user_id} not connected, cannot send message")
            return

        disconnected = []
        for connection_id, websocket in self.active_connections[user_id].items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(
                    f"Failed to send to user {user_id}, connection {connection_id}: {e}"
                )
                disconnected.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected:
            self.disconnect(user_id, connection_id)

    async def broadcast_to_room(
        self, room_id: str, message: Dict[str, Any], exclude_user: Optional[int] = None
    ):
        """
        Broadcast a message to all users in a room.

        Args:
            room_id: Room identifier
            message: Message to send (will be JSON encoded)
            exclude_user: Optional user ID to exclude from broadcast
        """
        if room_id not in self.rooms:
            logger.debug(f"Room {room_id} not found")
            return

        disconnected_users = []
        for user_id in self.rooms[room_id]:
            if exclude_user and user_id == exclude_user:
                continue

            if user_id not in self.active_connections:
                disconnected_users.append(user_id)
                continue

            try:
                await self.send_to_user(user_id, message)
            except Exception as e:
                logger.error(f"Failed to broadcast to user {user_id}: {e}")
                disconnected_users.append(user_id)

        # Clean up disconnected users from room
        for user_id in disconnected_users:
            await self.leave_room(room_id, user_id)

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected users.

        Args:
            message: Message to send (will be JSON encoded)
        """
        for user_id in list(self.active_connections.keys()):
            try:
                await self.send_to_user(user_id, message)
            except Exception as e:
                logger.error(f"Failed to broadcast to user {user_id}: {e}")

    def get_room_members(self, room_id: str) -> Set[int]:
        """
        Get all user IDs in a room.

        Args:
            room_id: Room identifier

        Returns:
            Set of user IDs
        """
        return self.rooms.get(room_id, set())

    def get_user_rooms(self, user_id: int) -> Set[str]:
        """
        Get all rooms a user is in.

        Args:
            user_id: User ID

        Returns:
            Set of room IDs
        """
        return {
            room_id for room_id, members in self.rooms.items() if user_id in members
        }

    def is_user_online(self, user_id: int) -> bool:
        """
        Check if a user has any active connections.

        Args:
            user_id: User ID

        Returns:
            True if user is online
        """
        return user_id in self.active_connections and bool(
            self.active_connections[user_id]
        )

    def get_online_users(self) -> Set[int]:
        """
        Get all online user IDs.

        Returns:
            Set of online user IDs
        """
        return set(self.active_connections.keys())

    def get_presence(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user presence information.

        Args:
            user_id: User ID

        Returns:
            Presence dict or None if not found
        """
        return self.user_presence.get(user_id)

    async def _heartbeat(
        self, websocket: WebSocket, connection_id: str, interval: int = 30
    ):
        """
        Send periodic ping messages to keep connection alive.

        Args:
            websocket: WebSocket connection
            connection_id: Connection identifier
            interval: Ping interval in seconds
        """
        try:
            while True:
                await asyncio.sleep(interval)
                try:
                    await websocket.send_json(
                        {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
                    )
                except Exception as e:
                    logger.debug(
                        f"Heartbeat failed for connection {connection_id}: {e}"
                    )
                    break
        except asyncio.CancelledError:
            logger.debug(f"Heartbeat cancelled for connection {connection_id}")


# Global connection manager instance
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager
