"""
Comprehensive test suite for Shadow Mode 7-day tracker functionality.
Tests session lifecycle, progress tracking, coin rewards, and edge cases.
"""

from fastapi.testclient import TestClient
from app.core.config import settings
from app.crud import user as crud_user
from app.schemas.user import UserCreate
from app.models.shadow_mode import ShadowModeSession


def test_start_shadow_session(client: TestClient, db):
    """Test starting a new shadow mode session."""
    # Create and login user
    email = "shadow@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Shadow User")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start shadow session
    r = client.post(
        f"{settings.API_V1_STR}/shadow-mode/start?day_number=1&total_goals=3",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "session" in data
    assert data["session"]["day_number"] == 1
    assert data["session"]["total_goals"] == 3
    assert "id" in data["session"]
    assert "start_time" in data["session"]


def test_start_session_with_active_session(client: TestClient, db):
    """Test that starting a session when one is active returns error."""
    # Create and login user
    email = "shadow2@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Shadow User 2")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start first session
    client.post(
        f"{settings.API_V1_STR}/shadow-mode/start?day_number=1&total_goals=3",
        headers=headers,
    )

    # Try to start second session
    r = client.post(
        f"{settings.API_V1_STR}/shadow-mode/start?day_number=2&total_goals=3",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "error" in data
    assert "already have an active session" in data["error"]


def test_end_shadow_session(client: TestClient, db):
    """Test ending a shadow mode session and coin calculation."""
    # Create and login user
    email = "shadow3@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Shadow User 3")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start session
    client.post(
        f"{settings.API_V1_STR}/shadow-mode/start?day_number=1&total_goals=5",
        headers=headers,
    )

    # End session with goals completed and focus score
    r = client.post(
        f"{settings.API_V1_STR}/shadow-mode/end?goals_completed=3&focus_score=8.5",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "session" in data
    assert data["session"]["goals_completed"] == 3
    assert data["session"]["total_goals"] == 5
    assert data["session"]["focus_score"] == 8.5
    assert "coins_earned" in data["session"]
    assert data["session"]["coins_earned"] > 0
    assert "duration_minutes" in data["session"]


def test_end_session_without_active(client: TestClient, db):
    """Test ending session when no active session exists."""
    # Create and login user
    email = "shadow4@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Shadow User 4")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try to end session without starting one
    r = client.post(
        f"{settings.API_V1_STR}/shadow-mode/end?goals_completed=3&focus_score=7.0",
        headers=headers,
    )
    assert r.status_code == 404
    assert "No active session found" in r.json()["detail"]


def test_get_shadow_progress(client: TestClient, db):
    """Test getting 7-day shadow mode progress."""
    # Create and login user
    email = "shadow5@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Shadow User 5")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create multiple sessions
    for day in range(1, 4):
        # Start session
        client.post(
            f"{settings.API_V1_STR}/shadow-mode/start?day_number={day}&total_goals=3",
            headers=headers,
        )
        # End session
        client.post(
            f"{settings.API_V1_STR}/shadow-mode/end?goals_completed=2&focus_score=7.0",
            headers=headers,
        )

    # Get progress
    r = client.get(f"{settings.API_V1_STR}/shadow-mode/progress", headers=headers)
    assert r.status_code == 200
    data = r.json()

    assert "completed_days" in data
    assert data["completed_days"] == 3
    assert data["total_days"] == 7
    assert "total_minutes" in data
    assert "avg_focus_score" in data
    assert len(data["sessions"]) == 3
    assert data["current_day"] is None  # No active session


def test_get_current_session(client: TestClient, db):
    """Test getting currently active shadow mode session."""
    # Create and login user
    email = "shadow6@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Shadow User 6")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get current session when none active
    r = client.get(f"{settings.API_V1_STR}/shadow-mode/current", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["active"] == False
    assert data["session"] is None

    # Start a session
    client.post(
        f"{settings.API_V1_STR}/shadow-mode/start?day_number=1&total_goals=5",
        headers=headers,
    )

    # Get current session when active
    r = client.get(f"{settings.API_V1_STR}/shadow-mode/current", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["active"] == True
    assert data["session"] is not None
    assert data["session"]["day_number"] == 1
    assert data["session"]["total_goals"] == 5
    assert "elapsed_minutes" in data["session"]


def test_coin_calculation_accuracy(client: TestClient, db):
    """Test that coin calculation is accurate based on completion and focus."""
    # Create and login user
    email = "shadow7@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Shadow User 7")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test case 1: 100% completion, high focus
    client.post(
        f"{settings.API_V1_STR}/shadow-mode/start?day_number=1&total_goals=10",
        headers=headers,
    )
    r = client.post(
        f"{settings.API_V1_STR}/shadow-mode/end?goals_completed=10&focus_score=10.0",
        headers=headers,
    )
    data = r.json()
    # Expected: (10/10) * 100 + 10.0 * 50 = 100 + 500 = 600 coins
    assert data["session"]["coins_earned"] == 600

    # Test case 2: 50% completion, moderate focus
    client.post(
        f"{settings.API_V1_STR}/shadow-mode/start?day_number=2&total_goals=4",
        headers=headers,
    )
    r = client.post(
        f"{settings.API_V1_STR}/shadow-mode/end?goals_completed=2&focus_score=5.0",
        headers=headers,
    )
    data = r.json()
    # Expected: (2/4) * 100 + 5.0 * 50 = 50 + 250 = 300 coins
    assert data["session"]["coins_earned"] == 300


def test_session_with_notes(client: TestClient, db):
    """Test that session notes are properly saved."""
    # Create and login user
    email = "shadow8@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Shadow User 8")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start session
    client.post(
        f"{settings.API_V1_STR}/shadow-mode/start?day_number=1&total_goals=3",
        headers=headers,
    )

    # End with notes
    notes_text = "Great focus session, completed all math problems"
    r = client.post(
        f"{settings.API_V1_STR}/shadow-mode/end?goals_completed=3&focus_score=9.0&notes={notes_text}",
        headers=headers,
    )
    assert r.status_code == 200

    # Verify session was saved with notes by checking database
    session = (
        db.query(ShadowModeSession).filter(ShadowModeSession.user_id == user.id).first()
    )
    assert session.notes == notes_text


def test_unauthorized_access(client: TestClient, db):
    """Test that endpoints require authentication."""
    # Try to access without token
    r = client.post(
        f"{settings.API_V1_STR}/shadow-mode/start?day_number=1&total_goals=3"
    )
    assert r.status_code == 401

    r = client.get(f"{settings.API_V1_STR}/shadow-mode/progress")
    assert r.status_code == 401

    r = client.get(f"{settings.API_V1_STR}/shadow-mode/current")
    assert r.status_code == 401
