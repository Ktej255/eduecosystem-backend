"""
WebSocket Integration Tests

Tests for real-time WebSocket functionality including discussions,
live classes, and notifications.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from app.models.user import User
from app.models.course import Course
from app.models.discussion import DiscussionThread, DiscussionCategory
from app.models.live_class import LiveClass
from app.core.security import create_access_token


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashedpassword123",
        is_active=True,
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_instructor(db: Session):
    """Create a test instructor."""
    user = User(
        email="instructor@example.com",
        username="instructor",
        hashed_password="hashedpassword123",
        is_active=True,
        role="instructor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_category(db: Session, test_course: Course):
    """Create a test discussion category."""
    category = DiscussionCategory(name="General", course_id=test_course.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def test_thread(
    db: Session, test_user: User, test_course: Course, test_category: DiscussionCategory
):
    """Create a test discussion thread."""
    thread = DiscussionThread(
        title="Test Thread",
        content="Test content",
        user_id=test_user.id,
        course_id=test_course.id,
        category_id=test_category.id,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


@pytest.fixture
def test_live_class(db: Session, test_instructor: User, test_course: Course):
    """Create a test live class session."""
    from datetime import datetime

    session = LiveClass(
        title="Test Live Class",
        instructor_id=test_instructor.id,
        course_id=test_course.id,
        scheduled_at=datetime.utcnow(),
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


class TestDiscussionWebSocket:
    """Tests for discussion WebSocket endpoints."""

    def test_websocket_connection_unauthorized(self):
        """Test WebSocket connection without authentication fails."""
        client = TestClient(app)

        with pytest.raises(Exception):
            with client.websocket_connect("/ws/discussions/1?token=invalidtoken"):
                pass

    def test_websocket_connection_authorized(
        self, test_user: User, test_thread: DiscussionThread
    ):
        """Test WebSocket connection with valid authentication."""
        client = TestClient(app)
        token = create_access_token(subject=test_user.id)

        with client.websocket_connect(
            f"/ws/discussions/{test_thread.id}?token={token}"
        ) as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data.get("type") in ["connected", "online_users"]

    def test_typing_indicator(self, test_user: User, test_thread: DiscussionThread):
        """Test typing indicator broadcast."""
        client = TestClient(app)
        token = create_access_token(subject=test_user.id)

        with client.websocket_connect(
            f"/ws/discussions/{test_thread.id}?token={token}"
        ) as websocket:
            # Skip initial messages
            websocket.receive_json()

            # Send typing event
            websocket.send_json({"type": "typing"})

            # Should broadcast to others (in real scenario with multiple connections)
            # For single connection test, just verify no errors

            # Send stop typing
            websocket.send_json({"type": "stop_typing"})

    def test_multiple_users_discussion(
        self, test_user: User, test_instructor: User, test_thread: DiscussionThread
    ):
        """Test multiple users in same discussion."""
        client = TestClient(app)
        token1 = create_access_token(subject=test_user.id)
        token2 = create_access_token(subject=test_instructor.id)

        with client.websocket_connect(
            f"/ws/discussions/{test_thread.id}?token={token1}"
        ) as ws1:
            with client.websocket_connect(
                f"/ws/discussions/{test_thread.id}?token={token2}"
            ) as ws2:
                # Both should receive connection confirmation
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()

                assert data1.get("type") is not None
                assert data2.get("type") is not None


class TestLiveClassWebSocket:
    """Tests for live class WebSocket endpoints."""

    def test_live_class_connection(self, test_user: User, test_live_class: LiveClass):
        """Test live class WebSocket connection."""
        client = TestClient(app)
        token = create_access_token(subject=test_user.id)

        with client.websocket_connect(
            f"/ws/live-class/{test_live_class.id}?token={token}"
        ) as websocket:
            # Should receive connection confirmation with participant count
            data = websocket.receive_json()
            assert data.get("type") == "connected"
            assert "participant_count" in data

    def test_chat_message_broadcast(self, test_user: User, test_live_class: LiveClass):
        """Test chat message broadcasting in live class."""
        client = TestClient(app)
        token = create_access_token(subject=test_user.id)

        with client.websocket_connect(
            f"/ws/live-class/{test_live_class.id}?token={token}"
        ) as websocket:
            # Skip connection message
            websocket.receive_json()

            # Send chat message
            websocket.send_json({"type": "chat_message", "message": "Hello everyone!"})

            # Should receive the broadcasted message
            data = websocket.receive_json()
            assert data.get("type") == "chat_message"
            assert data.get("message") == "Hello everyone!"

    def test_reaction_broadcast(self, test_user: User, test_live_class: LiveClass):
        """Test emoji reaction broadcasting."""
        client = TestClient(app)
        token = create_access_token(subject=test_user.id)

        with client.websocket_connect(
            f"/ws/live-class/{test_live_class.id}?token={token}"
        ) as websocket:
            # Skip connection message
            websocket.receive_json()

            # Send reaction
            websocket.send_json({"type": "reaction", "emoji": "👍"})

            # Should receive the broadcasted reaction
            data = websocket.receive_json()
            assert data.get("type") == "reaction"
            assert data.get("emoji") == "👍"

    def test_participant_tracking(
        self, test_user: User, test_instructor: User, test_live_class: LiveClass
    ):
        """Test participant count tracking."""
        client = TestClient(app)
        token1 = create_access_token(subject=test_user.id)
        token2 = create_access_token(subject=test_instructor.id)

        with client.websocket_connect(
            f"/ws/live-class/{test_live_class.id}?token={token1}"
        ) as ws1:
            # First user connects
            data1 = ws1.receive_json()
            initial_count = data1.get("participant_count", 0)

            with client.websocket_connect(
                f"/ws/live-class/{test_live_class.id}?token={token2}"
            ) as ws2:
                # Second user connects
                data2 = ws2.receive_json()

                # First user should receive participant update
                update1 = ws1.receive_json()
                assert update1.get("type") == "participant_update"
                assert update1.get("participant_count") > initial_count


class TestNotificationsWebSocket:
    """Tests for notifications WebSocket endpoint."""

    def test_notifications_connection(self, test_user: User):
        """Test notifications WebSocket connection."""
        client = TestClient(app)
        token = create_access_token(subject=test_user.id)

        with client.websocket_connect(f"/ws/notifications?token={token}") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data.get("type") == "connected"
            assert data.get("user_id") == test_user.id


class TestQuizWebSocket:
    """Tests for quiz WebSocket endpoint."""

    def test_quiz_connection(self, test_user: User, db: Session):
        """Test quiz WebSocket connection."""
        from app.models.quiz import Quiz

        # Create test quiz
        quiz = Quiz(title="Test Quiz", description="Test description", time_limit=30)
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        client = TestClient(app)
        token = create_access_token(subject=test_user.id)

        with client.websocket_connect(f"/ws/quiz/{quiz.id}?token={token}") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data.get("type") == "connected"

    def test_answer_submission_broadcast(self, test_user: User, db: Session):
        """Test answer submission broadcasting."""
        from app.models.quiz import Quiz

        # Create test quiz
        quiz = Quiz(title="Test Quiz", description="Test description", time_limit=30)
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        client = TestClient(app)
        token = create_access_token(subject=test_user.id)

        with client.websocket_connect(f"/ws/quiz/{quiz.id}?token={token}") as websocket:
            # Skip connection message
            websocket.receive_json()

            # Submit answer
            websocket.send_json({"type": "answer_submitted", "question_number": 1})

            # Should receive broadcast (without revealing answer)
            data = websocket.receive_json()
            assert data.get("type") == "user_answered"
            assert data.get("question_number") == 1


class TestWebSocketConnectionManager:
    """Tests for WebSocket connection manager utilities."""

    def test_heartbeat_mechanism(self, test_user: User, test_thread: DiscussionThread):
        """Test heartbeat/ping-pong mechanism."""
        client = TestClient(app)
        token = create_access_token(subject=test_user.id)

        with client.websocket_connect(
            f"/ws/discussions/{test_thread.id}?token={token}"
        ) as websocket:
            # Skip initial messages
            websocket.receive_json()

            # Send pong response
            websocket.send_json({"type": "pong"})

            # Should not disconnect
            # Wait for potential ping
            import time

            time.sleep(1)

    def test_connection_cleanup_on_disconnect(
        self, test_user: User, test_thread: DiscussionThread
    ):
        """Test connection cleanup on disconnect."""
        client = TestClient(app)
        token = create_access_token(subject=test_user.id)

        with client.websocket_connect(
            f"/ws/discussions/{test_thread.id}?token={token}"
        ) as websocket:
            data = websocket.receive_json()
            assert data is not None

        # Connection should be cleaned up after context exit
        # Reconnecting should work
        with client.websocket_connect(
            f"/ws/discussions/{test_thread.id}?token={token}"
        ) as websocket:
            data = websocket.receive_json()
            assert data is not None


@pytest.mark.asyncio
class TestRedisPubSub:
    """Tests for Redis Pub/Sub scaling functionality."""

    async def test_redis_pubsub_publish_subscribe(self):
        """Test Redis Pub/Sub message publishing and subscription."""
        from app.services.redis_pubsub import RedisPubSubService
        from app.core.config import settings

        pubsub = RedisPubSubService(settings.REDIS_URL)
        await pubsub.connect()

        if not pubsub.is_enabled():
            pytest.skip("Redis not available")

        received_messages = []

        async def message_handler(message):
            received_messages.append(message)

        # Subscribe to channel
        await pubsub.subscribe("test_channel", message_handler)

        # Publish message
        await pubsub.publish("test_channel", {"type": "test", "data": "hello"})

        # Wait for message propagation
        await asyncio.sleep(0.1)

        # Should have received the message
        assert len(received_messages) > 0
        assert received_messages[0]["type"] == "test"

        await pubsub.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
