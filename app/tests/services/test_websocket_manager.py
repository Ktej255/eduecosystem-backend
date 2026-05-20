import pytest
import asyncio

# Import the actual module to test
from app.services.websocket_manager import ConnectionManager

class MockWebSocket:
    def __init__(self, exception_on_send=False):
        self.accepted = False
        self.sent_messages = []
        self.exception_on_send = exception_on_send

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        if self.exception_on_send:
            raise Exception("Mock send error")
        self.sent_messages.append(message)


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def mock_ws():
    return MockWebSocket()

@pytest.mark.asyncio
async def test_connect(manager, mock_ws):
    user_id = 1
    connection_id = "conn1"
    metadata = {"device": "desktop"}

    await manager.connect(mock_ws, user_id, connection_id, metadata)

    assert mock_ws.accepted
    assert user_id in manager.active_connections
    assert connection_id in manager.active_connections[user_id]
    assert manager.active_connections[user_id][connection_id] == mock_ws

    # Check presence
    presence = manager.get_presence(user_id)
    assert presence is not None
    assert presence["status"] == "online"
    assert presence["metadata"] == metadata

    # Check heartbeat task
    assert connection_id in manager.heartbeat_tasks
    assert not manager.heartbeat_tasks[connection_id].done()

    # Cleanup to prevent dangling tasks
    manager.disconnect(user_id, connection_id)


@pytest.mark.asyncio
async def test_disconnect(manager, mock_ws):
    user_id = 1
    connection_id = "conn1"

    await manager.connect(mock_ws, user_id, connection_id)

    # Verify connected
    assert connection_id in manager.heartbeat_tasks
    task = manager.heartbeat_tasks[connection_id]

    # Disconnect
    manager.disconnect(user_id, connection_id)

    # Verify disconnected
    assert user_id not in manager.active_connections
    assert connection_id not in manager.heartbeat_tasks
    await asyncio.sleep(0)
    assert task.cancelled()

    # Check presence updated to offline
    presence = manager.get_presence(user_id)
    assert presence["status"] == "offline"


@pytest.mark.asyncio
async def test_disconnect_multiple_connections(manager):
    user_id = 1
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    await manager.connect(ws1, user_id, "conn1")
    await manager.connect(ws2, user_id, "conn2")

    # User has two connections
    assert len(manager.active_connections[user_id]) == 2

    # Disconnect one
    manager.disconnect(user_id, "conn1")

    # User still has one connection, presence should still be online (the method disconnect does not touch presence if connections remain)
    assert len(manager.active_connections[user_id]) == 1
    assert "conn2" in manager.active_connections[user_id]
    assert manager.get_presence(user_id)["status"] == "online"

    # Disconnect the other
    manager.disconnect(user_id, "conn2")
    assert user_id not in manager.active_connections
    assert manager.get_presence(user_id)["status"] == "offline"

@pytest.mark.asyncio
async def test_join_room(manager, mock_ws):
    room_id = "room1"
    user_id = 1

    # Needs to be connected first to receive the broadcast message properly
    await manager.connect(mock_ws, user_id, "conn1")

    # Clear initial messages
    mock_ws.sent_messages.clear()

    await manager.join_room(room_id, user_id)

    assert room_id in manager.rooms
    assert user_id in manager.rooms[room_id]

    # Broadcast goes to everyone in the room except the joining user
    # Here only user 1 is in the room and is excluded, so no message should be sent
    assert len(mock_ws.sent_messages) == 0


@pytest.mark.asyncio
async def test_join_room_broadcasts_to_others(manager):
    room_id = "room1"
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    await manager.connect(ws1, 1, "conn1")
    await manager.connect(ws2, 2, "conn2")

    await manager.join_room(room_id, 1)

    # Clear messages
    ws1.sent_messages.clear()
    ws2.sent_messages.clear()

    # User 2 joins
    await manager.join_room(room_id, 2)

    # User 1 should get user_joined message, User 2 shouldn't
    assert len(ws1.sent_messages) == 1
    assert ws1.sent_messages[0]["type"] == "user_joined"
    assert ws1.sent_messages[0]["user_id"] == 2
    assert len(ws2.sent_messages) == 0


@pytest.mark.asyncio
async def test_leave_room(manager):
    room_id = "room1"
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    await manager.connect(ws1, 1, "conn1")
    await manager.connect(ws2, 2, "conn2")

    await manager.join_room(room_id, 1)
    await manager.join_room(room_id, 2)

    # Clear messages
    ws1.sent_messages.clear()
    ws2.sent_messages.clear()

    # User 1 leaves
    await manager.leave_room(room_id, 1)

    # User 1 is removed
    assert 1 not in manager.rooms[room_id]
    assert 2 in manager.rooms[room_id]

    # User 2 should get user_left message
    assert len(ws2.sent_messages) == 1
    assert ws2.sent_messages[0]["type"] == "user_left"
    assert ws2.sent_messages[0]["user_id"] == 1


@pytest.mark.asyncio
async def test_leave_room_cleans_up_empty_rooms(manager, mock_ws):
    room_id = "room1"
    await manager.connect(mock_ws, 1, "conn1")
    await manager.join_room(room_id, 1)

    assert room_id in manager.rooms

    await manager.leave_room(room_id, 1)

    # Room should be deleted when empty
    assert room_id not in manager.rooms

@pytest.mark.asyncio
async def test_send_to_user(manager):
    user_id = 1
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    await manager.connect(ws1, user_id, "conn1")
    await manager.connect(ws2, user_id, "conn2")

    msg = {"type": "direct", "content": "hello"}
    await manager.send_to_user(user_id, msg)

    assert len(ws1.sent_messages) == 1
    assert ws1.sent_messages[0] == msg
    assert len(ws2.sent_messages) == 1
    assert ws2.sent_messages[0] == msg


@pytest.mark.asyncio
async def test_send_to_user_handles_disconnects(manager):
    user_id = 1
    # Create a websocket that raises an exception when sending
    ws_fail = MockWebSocket(exception_on_send=True)
    ws_ok = MockWebSocket()

    await manager.connect(ws_fail, user_id, "conn1")
    await manager.connect(ws_ok, user_id, "conn2")

    msg = {"type": "direct"}
    # The failing connection should raise an exception during send, which should be caught, and the connection disconnected.
    await manager.send_to_user(user_id, msg)

    # Check that ws_ok received the message
    assert len(ws_ok.sent_messages) == 1

    # Check that ws_fail was disconnected
    assert "conn1" not in manager.active_connections[user_id]
    assert "conn2" in manager.active_connections[user_id]


@pytest.mark.asyncio
async def test_broadcast_to_room(manager):
    room_id = "room1"
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    ws3 = MockWebSocket()

    await manager.connect(ws1, 1, "conn1")
    await manager.connect(ws2, 2, "conn2")
    await manager.connect(ws3, 3, "conn3")

    await manager.join_room(room_id, 1)
    await manager.join_room(room_id, 2)

    # Clear messages
    ws1.sent_messages.clear()
    ws2.sent_messages.clear()
    ws3.sent_messages.clear()

    msg = {"type": "room_msg"}
    await manager.broadcast_to_room(room_id, msg)

    # 1 and 2 should receive, 3 should not
    assert len(ws1.sent_messages) == 1
    assert len(ws2.sent_messages) == 1
    assert len(ws3.sent_messages) == 0


@pytest.mark.asyncio
async def test_broadcast_to_room_handles_disconnects(manager):
    room_id = "room1"
    # User 1 has a failing connection
    ws_fail = MockWebSocket(exception_on_send=True)
    ws_ok = MockWebSocket()

    await manager.connect(ws_fail, 1, "conn1")
    await manager.connect(ws_ok, 2, "conn2")

    await manager.join_room(room_id, 1)
    await manager.join_room(room_id, 2)

    msg = {"type": "room_msg"}
    await manager.broadcast_to_room(room_id, msg)

    # User 1 should be removed from the room due to failure
    assert 1 not in manager.rooms[room_id]
    assert 2 in manager.rooms[room_id]


@pytest.mark.asyncio
async def test_broadcast_to_all(manager):
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    await manager.connect(ws1, 1, "conn1")
    await manager.connect(ws2, 2, "conn2")

    msg = {"type": "broadcast"}
    await manager.broadcast_to_all(msg)

    assert len(ws1.sent_messages) == 1
    assert len(ws2.sent_messages) == 1

@pytest.mark.asyncio
async def test_helper_methods(manager):
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    await manager.connect(ws1, 1, "conn1")
    await manager.connect(ws2, 2, "conn2")

    await manager.join_room("roomA", 1)
    await manager.join_room("roomA", 2)
    await manager.join_room("roomB", 1)

    # test get_room_members
    assert manager.get_room_members("roomA") == {1, 2}
    assert manager.get_room_members("roomB") == {1}
    assert manager.get_room_members("nonexistent") == set()

    # test get_user_rooms
    assert manager.get_user_rooms(1) == {"roomA", "roomB"}
    assert manager.get_user_rooms(2) == {"roomA"}
    assert manager.get_user_rooms(3) == set()

    # test is_user_online
    assert manager.is_user_online(1) is True
    assert manager.is_user_online(3) is False

    # test get_online_users
    assert manager.get_online_users() == {1, 2}
