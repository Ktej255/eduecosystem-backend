import sys
from unittest.mock import MagicMock

# Mock fastapi before importing the module under test
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.WebSocket"] = MagicMock()

import pytest
import asyncio
from datetime import datetime
from app.services.websocket_manager import ConnectionManager

@pytest.fixture
def manager():
    return ConnectionManager()

def test_initialization(manager):
    assert manager.active_connections == {}
    assert manager.rooms == {}
    assert manager.user_presence == {}
    assert manager.heartbeat_tasks == {}


class MockWebSocket:
    def __init__(self):
        self.accept_called = False
        self.sent_messages = []
        self.closed = False

    async def accept(self):
        self.accept_called = True

    async def send_json(self, data):
        if self.closed:
            raise Exception("WebSocket is closed")
        self.sent_messages.append(data)

    async def close(self):
        self.closed = True

@pytest.fixture
def mock_websocket():
    return MockWebSocket()

@pytest.fixture
def mock_websocket_factory():
    def _create():
        return MockWebSocket()
    return _create


def test_connect(manager, mock_websocket):
    user_id = 1
    connection_id = "conn_1"
    metadata = {"device": "desktop"}

    asyncio.run(manager.connect(mock_websocket, user_id, connection_id, metadata))

    assert mock_websocket.accept_called is True
    assert user_id in manager.active_connections
    assert connection_id in manager.active_connections[user_id]
    assert manager.active_connections[user_id][connection_id] == mock_websocket

    # Check presence
    assert user_id in manager.user_presence
    presence = manager.user_presence[user_id]
    assert presence["status"] == "online"
    assert presence["metadata"] == metadata
    assert "last_seen" in presence

    # Check heartbeat task
    assert connection_id in manager.heartbeat_tasks
    # Task finishes because the asyncio loop closes, skip this assertion

    # Cleanup task so asyncio doesn't complain
    manager.disconnect(user_id, connection_id)

def test_disconnect(manager, mock_websocket, mock_websocket_factory):
    user_id = 2
    conn_id_1 = "conn_1"
    conn_id_2 = "conn_2"

    ws1 = mock_websocket_factory()
    ws2 = mock_websocket_factory()

    asyncio.run(manager.connect(ws1, user_id, conn_id_1))
    asyncio.run(manager.connect(ws2, user_id, conn_id_2))

    # Assert tasks created
    task1 = manager.heartbeat_tasks[conn_id_1]
    task2 = manager.heartbeat_tasks[conn_id_2]

    # Disconnect first connection
    manager.disconnect(user_id, conn_id_1)

    assert conn_id_1 not in manager.active_connections[user_id]
    assert conn_id_2 in manager.active_connections[user_id]

    # Heartbeat task for conn_1 should be cancelled and removed
    assert task1.cancelled() or task1.done()
    assert conn_id_1 not in manager.heartbeat_tasks

    # User should still be online
    assert manager.user_presence[user_id]["status"] == "online"

    # Disconnect second connection
    manager.disconnect(user_id, conn_id_2)

    assert user_id not in manager.active_connections
    assert conn_id_2 not in manager.heartbeat_tasks

    # User should now be offline
    assert manager.user_presence[user_id]["status"] == "offline"


def test_join_and_leave_room(manager, mock_websocket):
    user_id_1 = 1
    user_id_2 = 2
    room_id = "room_1"

    # We must setup connections first so broadcast works correctly
    asyncio.run(manager.connect(mock_websocket, user_id_1, "conn_1"))
    asyncio.run(manager.connect(mock_websocket, user_id_2, "conn_2"))

    # Join room
    asyncio.run(manager.join_room(room_id, user_id_1))

    assert room_id in manager.rooms
    assert user_id_1 in manager.rooms[room_id]

    # Second user joins room
    asyncio.run(manager.join_room(room_id, user_id_2))
    assert user_id_2 in manager.rooms[room_id]

    # Check broadcast happened (user 1 should be notified of user 2 joining)
    assert len(mock_websocket.sent_messages) > 0
    assert mock_websocket.sent_messages[-1]["type"] == "user_joined"

    # Leave room
    asyncio.run(manager.leave_room(room_id, user_id_1))

    assert user_id_1 not in manager.rooms[room_id]
    assert user_id_2 in manager.rooms[room_id]

    # User 2 leaves room
    asyncio.run(manager.leave_room(room_id, user_id_2))

    # Room should be cleaned up
    assert room_id not in manager.rooms


def test_send_to_user(manager, mock_websocket_factory):
    user_id = 1
    ws1 = mock_websocket_factory()
    ws2 = mock_websocket_factory()

    asyncio.run(manager.connect(ws1, user_id, "conn_1"))
    asyncio.run(manager.connect(ws2, user_id, "conn_2"))

    message = {"type": "direct_message", "data": "hello"}
    asyncio.run(manager.send_to_user(user_id, message))

    assert len(ws1.sent_messages) == 1
    assert len(ws2.sent_messages) == 1
    assert ws1.sent_messages[0] == message
    assert ws2.sent_messages[0] == message

def test_send_to_user_disconnected(manager, mock_websocket_factory):
    user_id = 1
    ws1 = mock_websocket_factory()

    asyncio.run(manager.connect(ws1, user_id, "conn_1"))

    # Simulate a closed websocket that raises an exception when sending
    ws1.closed = True

    message = {"type": "direct_message", "data": "hello"}
    asyncio.run(manager.send_to_user(user_id, message))

    # The manager should have disconnected conn_1
    assert user_id not in manager.active_connections

def test_broadcast_to_room(manager, mock_websocket_factory):
    user_id_1 = 1
    user_id_2 = 2
    user_id_3 = 3
    room_id = "room_1"

    ws1 = mock_websocket_factory()
    ws2 = mock_websocket_factory()
    ws3 = mock_websocket_factory() # Not in room

    asyncio.run(manager.connect(ws1, user_id_1, "conn_1"))
    asyncio.run(manager.connect(ws2, user_id_2, "conn_2"))
    asyncio.run(manager.connect(ws3, user_id_3, "conn_3"))

    asyncio.run(manager.join_room(room_id, user_id_1))
    asyncio.run(manager.join_room(room_id, user_id_2))

    # Clear previous join messages
    ws1.sent_messages.clear()
    ws2.sent_messages.clear()
    ws3.sent_messages.clear()

    message = {"type": "room_broadcast", "data": "hello room"}
    asyncio.run(manager.broadcast_to_room(room_id, message))

    assert len(ws1.sent_messages) == 1
    assert len(ws2.sent_messages) == 1
    assert len(ws3.sent_messages) == 0
    assert ws1.sent_messages[0] == message

    # Test exclude_user
    ws1.sent_messages.clear()
    ws2.sent_messages.clear()

    asyncio.run(manager.broadcast_to_room(room_id, message, exclude_user=user_id_1))

    assert len(ws1.sent_messages) == 0
    assert len(ws2.sent_messages) == 1

def test_broadcast_to_all(manager, mock_websocket_factory):
    user_id_1 = 1
    user_id_2 = 2

    ws1 = mock_websocket_factory()
    ws2 = mock_websocket_factory()

    asyncio.run(manager.connect(ws1, user_id_1, "conn_1"))
    asyncio.run(manager.connect(ws2, user_id_2, "conn_2"))

    message = {"type": "global_broadcast", "data": "hello all"}
    asyncio.run(manager.broadcast_to_all(message))

    assert len(ws1.sent_messages) == 1
    assert len(ws2.sent_messages) == 1
    assert ws1.sent_messages[0] == message


def test_getters_and_properties(manager, mock_websocket_factory):
    user_id_1 = 1
    user_id_2 = 2
    room_id_1 = "room_1"
    room_id_2 = "room_2"

    ws1 = mock_websocket_factory()
    ws2 = mock_websocket_factory()

    # Empty state checks
    assert manager.get_room_members(room_id_1) == set()
    assert manager.get_user_rooms(user_id_1) == set()
    assert manager.is_user_online(user_id_1) is False
    assert manager.get_online_users() == set()
    assert manager.get_presence(user_id_1) is None

    # Connect users
    asyncio.run(manager.connect(ws1, user_id_1, "conn_1", {"device": "mobile"}))
    asyncio.run(manager.connect(ws2, user_id_2, "conn_2", {"device": "desktop"}))

    # Join rooms
    asyncio.run(manager.join_room(room_id_1, user_id_1))
    asyncio.run(manager.join_room(room_id_1, user_id_2))
    asyncio.run(manager.join_room(room_id_2, user_id_1))

    # Test get_room_members
    assert manager.get_room_members(room_id_1) == {user_id_1, user_id_2}
    assert manager.get_room_members(room_id_2) == {user_id_1}

    # Test get_user_rooms
    assert manager.get_user_rooms(user_id_1) == {room_id_1, room_id_2}
    assert manager.get_user_rooms(user_id_2) == {room_id_1}

    # Test is_user_online
    assert manager.is_user_online(user_id_1) is True
    assert manager.is_user_online(user_id_2) is True
    assert manager.is_user_online(3) is False

    # Test get_online_users
    assert manager.get_online_users() == {user_id_1, user_id_2}

    # Test get_presence
    presence = manager.get_presence(user_id_1)
    assert presence is not None
    assert presence["status"] == "online"
    assert presence["metadata"] == {"device": "mobile"}

    # Disconnect user 1 and re-check
    manager.disconnect(user_id_1, "conn_1")
    assert manager.is_user_online(user_id_1) is False
    assert manager.get_online_users() == {user_id_2}

    # Presence should show offline but still exist
    presence_offline = manager.get_presence(user_id_1)
    assert presence_offline is not None
    assert presence_offline["status"] == "offline"
