import sys
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
import asyncio
import json

# Safely handle the redis module import for the sandbox environment
# In a real environment, redis would be installed.
try:
    import redis
    import redis.asyncio
except ImportError:
    # We only mock it in sys.modules if it's truly missing,
    # but we should ensure we clean it up or handle it more gracefully
    # For now, we will rely purely on `patch` inside the tests where needed,
    # but if the module itself can't be imported by `app.services.redis_pubsub`,
    # we need to provide a dummy module.
    mock_redis_module = MagicMock()
    mock_redis_asyncio = MagicMock()

    class RedisError(Exception):
        pass

    mock_redis_module.RedisError = RedisError
    mock_redis_asyncio.RedisError = RedisError

    sys.modules["redis"] = mock_redis_module
    sys.modules["redis.asyncio"] = mock_redis_asyncio

from app.services.redis_pubsub import RedisPubSubService, init_pubsub, get_pubsub

class MockPubSub:
    def __init__(self):
        self.channels = set()
        self.messages = []
        self._listen_queue = asyncio.Queue()
        self.closed = False

    async def subscribe(self, channel):
        self.channels.add(channel)

    async def unsubscribe(self, channel):
        if channel in self.channels:
            self.channels.remove(channel)

    async def close(self):
        self.closed = True

    async def listen(self):
        while not self.closed:
            try:
                # Wait for next message or cancellation
                msg = await self._listen_queue.get()
                if msg is None:
                    break
                yield msg
            except asyncio.CancelledError:
                break

    async def put_message(self, message):
        await self._listen_queue.put(message)

class MockRedisClient:
    def __init__(self):
        self.published = []
        self.mock_pubsub = MockPubSub()
        self.closed = False

    async def ping(self):
        # Allow it to be awaited in asyncio.wait_for
        await asyncio.sleep(0)
        return True

    def pubsub(self):
        return self.mock_pubsub

    async def publish(self, channel, message):
        self.published.append({"channel": channel, "message": message})
        return 1

    async def close(self):
        self.closed = True
        await self.mock_pubsub.close()

@pytest.fixture
def mock_redis():
    client = MockRedisClient()
    with patch("app.services.redis_pubsub.redis.from_url", return_value=client) as mock_from_url:
        yield client

@pytest.fixture
async def pubsub_service(mock_redis):
    service = RedisPubSubService("redis://localhost:6379")
    with patch("app.services.redis_pubsub.redis.from_url", return_value=mock_redis):
        await service.connect()
    yield service
    await service.disconnect()

@pytest.mark.asyncio
async def test_connect(mock_redis):
    service = RedisPubSubService("redis://localhost:6379")
    with patch("app.services.redis_pubsub.redis.from_url", return_value=mock_redis):
        await service.connect()

    assert service.is_enabled() is True
    assert service.redis_client == mock_redis
    assert service.pubsub == mock_redis.mock_pubsub

    await service.disconnect()

@pytest.mark.asyncio
async def test_connect_failure():
    service = RedisPubSubService("redis://localhost:6379")

    with patch("app.services.redis_pubsub.redis.from_url", side_effect=Exception("Connection error")):
        await service.connect()

    assert service.is_enabled() is False

@pytest.mark.asyncio
async def test_disconnect(mock_redis):
    service = RedisPubSubService("redis://localhost:6379")
    with patch("app.services.redis_pubsub.redis.from_url", return_value=mock_redis):
        await service.connect()

    assert service.is_enabled() is True

    await service.disconnect()

    assert service.is_enabled() is False
    assert mock_redis.closed is True
    assert mock_redis.mock_pubsub.closed is True

@pytest.mark.asyncio
async def test_publish(pubsub_service, mock_redis):
    channel = "test_channel"
    message = {"type": "test", "data": "hello"}

    await pubsub_service.publish(channel, message)

    assert len(mock_redis.published) == 1
    assert mock_redis.published[0]["channel"] == channel
    assert json.loads(mock_redis.published[0]["message"]) == message

@pytest.mark.asyncio
async def test_publish_not_enabled():
    service = RedisPubSubService("redis://localhost:6379")
    # Not connected

    await service.publish("channel", {"data": "test"})
    # Should not raise exception

@pytest.mark.asyncio
async def test_subscribe_unsubscribe(pubsub_service, mock_redis):
    channel = "test_channel"
    received_messages = []

    async def callback(msg):
        received_messages.append(msg)

    await pubsub_service.subscribe(channel, callback)

    assert channel in pubsub_service.subscriptions
    assert channel in mock_redis.mock_pubsub.channels
    assert pubsub_service.listener_task is not None
    assert not pubsub_service.listener_task.done()

    await pubsub_service.unsubscribe(channel)

    assert channel not in pubsub_service.subscriptions
    assert channel not in mock_redis.mock_pubsub.channels

@pytest.mark.asyncio
async def test_listen(pubsub_service, mock_redis):
    channel = "test_channel"
    received_messages = []

    async def callback(msg):
        received_messages.append(msg)

    await pubsub_service.subscribe(channel, callback)

    # Simulate message coming from Redis
    message = {
        "type": "message",
        "channel": channel,
        "data": json.dumps({"test": "data"})
    }
    await mock_redis.mock_pubsub.put_message(message)

    # Let event loop run slightly so listener task can process it
    await asyncio.sleep(0.1)

    assert len(received_messages) == 1
    assert received_messages[0] == {"test": "data"}

@pytest.mark.asyncio
async def test_listen_invalid_json(pubsub_service, mock_redis):
    channel = "test_channel"
    received_messages = []

    async def callback(msg):
        received_messages.append(msg)

    await pubsub_service.subscribe(channel, callback)

    # Simulate invalid message
    message = {
        "type": "message",
        "channel": channel,
        "data": "invalid json"
    }
    await mock_redis.mock_pubsub.put_message(message)

    # Let event loop run slightly
    await asyncio.sleep(0.1)

    # Should not have crashed, but should not have called callback
    assert len(received_messages) == 0
    assert not pubsub_service.listener_task.done()

@pytest.mark.asyncio
async def test_global_init_pubsub():
    with patch("app.services.redis_pubsub.redis.from_url", return_value=MockRedisClient()):
        # reset global state for test
        import app.services.redis_pubsub as rp
        rp._pubsub_service = None

        service = await init_pubsub("redis://localhost:6379")

        assert service is not None
        assert service.is_enabled() is True

        retrieved = get_pubsub()
        assert retrieved is service

        await service.disconnect()
