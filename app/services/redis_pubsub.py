"""
Redis Pub/Sub Service

Enables horizontal scaling of WebSocket connections across multiple server instances.
Messages are published to Redis channels and subscribers receive them.
"""

import json
import logging
import asyncio
from typing import Callable, Dict, Any, Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisPubSubService:
    """
    Redis Pub/Sub service for cross-server WebSocket message broadcasting.
    """

    def __init__(self, redis_url: str):
        """
        Initialize Redis Pub/Sub service.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscriptions: Dict[str, Callable] = {}
        self.listener_task: Optional[asyncio.Task] = None
        self.enabled = False

    async def connect(self):
        """
        Connect to Redis and initialize Pub/Sub.
        """
        try:
            self.redis_client = redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )

            # Test connection with timeout
            await asyncio.wait_for(self.redis_client.ping(), timeout=2.0)

            self.pubsub = self.redis_client.pubsub()
            self.enabled = True

            logger.info("Redis Pub/Sub service initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize Redis Pub/Sub: {e}")
            self.enabled = False

    async def disconnect(self):
        """
        Disconnect from Redis and clean up resources.
        """
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            await self.pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        self.enabled = False
        logger.info("Redis Pub/Sub service disconnected")

    async def publish(self, channel: str, message: Dict[str, Any]):
        """
        Publish a message to a Redis channel.

        Args:
            channel: Channel name
            message: Message to publish (will be JSON encoded)
        """
        if not self.enabled or not self.redis_client:
            logger.debug("Redis Pub/Sub not enabled, skipping publish")
            return

        try:
            message_json = json.dumps(message)
            await self.redis_client.publish(channel, message_json)
            logger.debug(
                f"Published to channel {channel}: {message.get('type', 'unknown')}"
            )
        except Exception as e:
            logger.error(f"Failed to publish to channel {channel}: {e}")

    async def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Subscribe to a Redis channel.

        Args:
            channel: Channel name
            callback: Async function to call when message received
        """
        if not self.enabled or not self.pubsub:
            logger.warning(f"Redis Pub/Sub not enabled, cannot subscribe to {channel}")
            return

        try:
            await self.pubsub.subscribe(channel)
            self.subscriptions[channel] = callback

            # Start listener task if not already running
            if not self.listener_task or self.listener_task.done():
                self.listener_task = asyncio.create_task(self._listen())

            logger.info(f"Subscribed to channel: {channel}")

        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")

    async def unsubscribe(self, channel: str):
        """
        Unsubscribe from a Redis channel.

        Args:
            channel: Channel name
        """
        if not self.enabled or not self.pubsub:
            return

        try:
            await self.pubsub.unsubscribe(channel)
            if channel in self.subscriptions:
                del self.subscriptions[channel]

            logger.info(f"Unsubscribed from channel: {channel}")

        except Exception as e:
            logger.error(f"Failed to unsubscribe from channel {channel}: {e}")

    async def _listen(self):
        """
        Listen for messages on subscribed channels.
        """
        if not self.pubsub:
            return

        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data = message["data"]

                    try:
                        # Parse JSON message
                        message_data = json.loads(data)

                        # Call the callback for this channel
                        if channel in self.subscriptions:
                            callback = self.subscriptions[channel]
                            await callback(message_data)

                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in message from {channel}: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message from {channel}: {e}")

        except asyncio.CancelledError:
            logger.info("Redis Pub/Sub listener cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in Redis Pub/Sub listener: {e}")

    def is_enabled(self) -> bool:
        """Check if Redis Pub/Sub is enabled."""
        return self.enabled


# Global Redis Pub/Sub instance
_pubsub_service: Optional[RedisPubSubService] = None


async def init_pubsub(redis_url: str) -> RedisPubSubService:
    """
    Initialize the global Redis Pub/Sub service.

    Args:
        redis_url: Redis connection URL

    Returns:
        RedisPubSubService instance
    """
    global _pubsub_service

    if _pubsub_service is None:
        _pubsub_service = RedisPubSubService(redis_url)
        await _pubsub_service.connect()

    return _pubsub_service


def get_pubsub() -> Optional[RedisPubSubService]:
    """
    Get the global Redis Pub/Sub service instance.

    Returns:
        RedisPubSubService instance or None if not initialized
    """
    return _pubsub_service
