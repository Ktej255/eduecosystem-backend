import pytest
import asyncio
from app.core.websocket import manager


@pytest.mark.asyncio
async def test_websocket_manager_connection():
    """Test basic connection handling"""

    # Mock WebSocket
    class MockWebSocket:
        def __init__(self):
            self.accepted = False
            self.closed = False
            self.sent_messages = []

        async def accept(self):
            self.accepted = True

        async def send_json(self, message):
            self.sent_messages.append(message)

        async def send_text(self, message):
            self.sent_messages.append(message)

        async def close(self):
            self.closed = True

    ws = MockWebSocket()
    room = "test_room"
    user_id = 1
    user_name = "Test User"

    # Test Connect
    await manager.connect(ws, room, user_id, user_name)

    assert ws.accepted
    assert room in manager.active_connections
    assert ws in manager.active_connections[room]
    assert manager.get_room_count(room) == 1

    # Test Disconnect
    manager.disconnect(ws)
    assert room not in manager.active_connections
    assert manager.get_room_count(room) == 0


@pytest.mark.asyncio
async def test_websocket_broadcast():
    """Test message broadcasting"""

    class MockWebSocket:
        def __init__(self):
            self.sent_messages = []

        async def accept(self):
            pass

        async def send_json(self, message):
            self.sent_messages.append(message)

        async def send_text(self, message):
            self.sent_messages.append(message)

        async def close(self):
            pass

    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    room = "broadcast_room"

    await manager.connect(ws1, room, 1, "User 1")
    await manager.connect(ws2, room, 2, "User 2")

    message = {"type": "test", "content": "hello"}

    # Test Broadcast
    await manager.broadcast_to_room(room, message)

    # Check if messages were sent (serialized as text)
    assert len(ws1.sent_messages) >= 1
    assert len(ws2.sent_messages) >= 1

    # Verify content (checking substring as it's serialized)
    assert "hello" in str(ws1.sent_messages[-1])
    assert "hello" in str(ws2.sent_messages[-1])

    manager.disconnect(ws1)
    manager.disconnect(ws2)


@pytest.mark.asyncio
async def test_websocket_batching():
    """Test message batching"""

    class MockWebSocket:
        def __init__(self):
            self.sent_messages = []

        async def accept(self):
            pass

        async def send_json(self, message):
            self.sent_messages.append(message)

        async def send_text(self, message):
            self.sent_messages.append(message)

        async def close(self):
            pass

    ws = MockWebSocket()
    room = "batch_room"

    await manager.connect(ws, room, 1, "User 1")

    # Queue messages
    msg1 = {"type": "update", "id": 1}
    msg2 = {"type": "update", "id": 2}

    await manager.broadcast_to_room(room, msg1, batch=True)
    await manager.broadcast_to_room(room, msg2, batch=True)

    # Verify queue
    assert room in manager.message_queue
    assert len(manager.message_queue[room]) == 2

    # Wait for batch processor (it runs every 0.1s)
    await asyncio.sleep(0.2)

    # Verify messages sent
    assert len(ws.sent_messages) >= 2

    manager.disconnect(ws)
