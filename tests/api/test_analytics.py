"""
Comprehensive test suite for Analytics dashboard functionality.
Tests data aggregation, insights generation, and statistics accuracy.
"""

from fastapi.testclient import TestClient
from app.core.config import settings
from app.crud import user as crud_user
from app.schemas.user import UserCreate
from app.models.shadow_mode import ShadowModeSession
from app.models.submission import HandwritingSubmission
from app.models.activity_log import ActivityLog  
from datetime import datetime, timezone, timedelta
import pytest


def test_dashboard_analytics_basic(client: TestClient, db):
    """Test basic dashboard analytics retrieval."""
    # Create and login user
    email = "analytics1@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Analytics User 1")
    user = crud_user.create(db, obj_in=user_in)
    user.coins = 250
    user.streak_days = 5
    # Set last login to yesterday so streak is maintained
    user.last_login = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get dashboard analytics
    r = client.get(f"{settings.API_V1_STR}/analytics/dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()

    # Verify structure
    assert "user" in data
    # User gets +5 coins for daily login and +10 for streak maintenance
    assert data["user"]["coins"] == 265
    # Streak increments from 5 to 6 on consecutive day login
    assert data["user"]["streak_days"] == 6
    assert data["user"]["full_name"] == "Analytics User 1"

    assert "shadow_mode" in data
    assert "completed_days" in data["shadow_mode"]
    assert "total_days" in data["shadow_mode"]
    assert data["shadow_mode"]["total_days"] == 7

    assert "attention" in data
    assert "total_checks" in data["attention"]
    assert "average_focus" in data["attention"]

    assert "handwriting" in data
    assert "total_submissions" in data["handwriting"]

    assert "weekly_activity" in data
    assert "insights" in data
    assert isinstance(data["insights"], list)


def test_analytics_with_shadow_sessions(client: TestClient, db):
    """Test analytics correctly aggregates shadow mode data."""
    # Create and login user
    email = "analytics2@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Analytics User 2")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create 3 completed shadow sessions
    for i in range(3):
        session = ShadowModeSession(
            user_id=user.id,
            day_number=i + 1,
            total_goals=5,
            goals_completed=3,
            focus_score=8.0,
            duration_minutes=60,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            is_active=False,
        )
        db.add(session)
    db.commit()

    # Get analytics
    r = client.get(f"{settings.API_V1_STR}/analytics/dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()

    shadow_data = data["shadow_mode"]
    assert shadow_data["completed_days"] == 3
    assert shadow_data["total_minutes"] == 180  # 60 * 3
    assert shadow_data["avg_focus_score"] == 8.0


def test_analytics_handwriting_count(client: TestClient, db):
    """Test analytics counts handwriting submissions correctly."""
    # Create and login user
    email = "analytics3@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Analytics User 3")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create handwriting submissions
    for i in range(5):
        submission = HandwritingSubmission(
            user_id=user.id,
            image_url=f"test_{i}.jpg",
            report_content="Sample text",
            report_level="AI Analysis",
        )
        db.add(submission)
    db.commit()

    # Get analytics
    r = client.get(f"{settings.API_V1_STR}/analytics/dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()

    assert data["handwriting"]["total_submissions"] == 5


def test_analytics_insights_generation(client: TestClient, db):
    """Test that insights are generated correctly."""
    # Create and login user
    email = "analytics4@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Analytics User 4")
    user = crud_user.create(db, obj_in=user_in)
    user.coins = 750
    user.streak_days = 12
    db.commit()

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get analytics
    r = client.get(f"{settings.API_V1_STR}/analytics/dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()

    insights = data["insights"]
    assert len(insights) > 0

    # Check insight structure
    for insight in insights:
        assert "title" in insight
        assert "description" in insight
        assert "type" in insight
        assert insight["type"] in ["info", "success", "goal", "warning"]

    # Check for streak mention in insights
    streak_mentioned = any(
        str(user.streak_days) in insight["description"] for insight in insights
    )
    assert streak_mentioned


def test_analytics_attention_tracking(client: TestClient, db):
    """Test attention tracking statistics in analytics."""
    # Create and login user
    email = "analytics5@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Analytics User 5")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create attention check logs
    attention_scores = [7.5, 8.0, 6.5, 9.0, 7.0]
    for score in attention_scores:
        log = ActivityLog(
            user_id=user.id,
            action="attention_check",
            details=str(score),
            timestamp=datetime.now(timezone.utc),
        )
        db.add(log)
    db.commit()

    # Get analytics
    r = client.get(f"{settings.API_V1_STR}/analytics/dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()

    attention_data = data["attention"]
    assert attention_data["total_checks"] == 5
    expected_avg = sum(attention_scores) / len(attention_scores)
    assert abs(attention_data["average_focus"] - expected_avg) < 0.1
    assert len(attention_data["recent_scores"]) <= 10


@pytest.mark.skip(reason="Endpoint /analytics/detailed not yet implemented")
def test_detailed_analytics(client: TestClient, db):
    """Test detailed analytics endpoint with advanced charts."""
    # Create and login user
    email = "analytics6@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Analytics User 6")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get detailed analytics
    r = client.get(f"{settings.API_V1_STR}/analytics/detailed", headers=headers)
    assert r.status_code == 200
    data = r.json()

    # Verify structure
    assert "skills" in data
    assert isinstance(data["skills"], list)
    assert len(data["skills"]) > 0

    # Check skills radar structure
    for skill in data["skills"]:
        assert "subject" in skill
        assert "A" in skill
        assert "fullMark" in skill

    assert "heatmap" in data
    assert isinstance(data["heatmap"], list)

    assert "comparative" in data
    assert "user_focus" in data["comparative"]
    assert "global_focus" in data["comparative"]
    assert "user_percentile" in data["comparative"]


def test_analytics_with_activity_heatmap(client: TestClient, db):
    """Test activity heatmap data generation."""
    # Create and login user
    email = "analytics7@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Analytics User 7")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create activity logs on different days
    for i in range(10):
        log = ActivityLog(
            user_id=user.id,
            action="login",
            details="User logged in",
            timestamp=datetime.now(timezone.utc),
        )
        db.add(log)
    db.commit()

    # Get detailed analytics
    r = client.get(f"{settings.API_V1_STR}/analytics/detailed", headers=headers)
    assert r.status_code == 200
    data = r.json()

    heatmap = data["heatmap"]
    # Should have at least some data
    assert isinstance(heatmap, list)

    # Each heatmap entry should have date and count
    for entry in heatmap:
        assert "date" in entry
        assert "count" in entry
        assert entry["count"] > 0


def test_analytics_empty_state(client: TestClient, db):
    """Test analytics for new user with no activity."""
    # Create and login user
    email = "newuser@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="New User")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get analytics
    r = client.get(f"{settings.API_V1_STR}/analytics/dashboard", headers=headers)
    assert r.status_code == 200
    data = r.json()

    # Should handle empty data gracefully
    assert data["shadow_mode"]["completed_days"] == 0
    assert data["shadow_mode"]["total_minutes"] == 0
    assert data["shadow_mode"]["avg_focus_score"] == 0
    assert data["attention"]["total_checks"] == 0
    assert data["attention"]["average_focus"] == 0
    assert data["handwriting"]["total_submissions"] == 0


def test_unauthorized_analytics_access(client: TestClient, db):
    """Test that analytics endpoints require authentication."""
    # Try to access without token
    r = client.get(f"{settings.API_V1_STR}/analytics/dashboard")
    assert r.status_code == 401

    r = client.get(f"{settings.API_V1_STR}/analytics/detailed")
    assert r.status_code == 401
