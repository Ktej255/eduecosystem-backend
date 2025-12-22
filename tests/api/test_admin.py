"""
Comprehensive test suite for Admin panel functionality.
Tests admin authentication, user management, stats, permissions, and audit logging.
"""

from fastapi.testclient import TestClient
from app.core.config import settings
from app.crud import user as crud_user
from app.schemas.user import UserCreate
from app.models.admin_log import AdminLog
from app.models.submission import HandwritingSubmission
from app.models.shadow_mode import ShadowModeSession


def create_admin_user(db, email="admin@example.com"):
    """Helper to create an admin user."""
    user_in = UserCreate(email=email, password="admin123", full_name="Admin User")
    user = crud_user.create(db, obj_in=user_in)
    user.role = "admin"
    db.commit()
    db.refresh(user)
    return user


def create_regular_user(db, email="user@example.com"):
    """Helper to create a regular user."""
    user_in = UserCreate(email=email, password="user123", full_name="Regular User")
    user = crud_user.create(db, obj_in=user_in)
    db.refresh(user)
    return user


def test_admin_stats_endpoint(client: TestClient, db):
    """Test admin platform statistics endpoint."""
    # Create admin user
    admin = create_admin_user(db, "admin1@example.com")

    # Login as admin
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin1@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create some test data
    create_regular_user(db, "testuser1@example.com")
    create_regular_user(db, "testuser2@example.com")

    # Get admin stats
    r = client.get(f"{settings.API_V1_STR}/admin/stats", headers=headers)
    assert r.status_code == 200
    data = r.json()

    # Verify structure
    assert "users" in data
    assert "total" in data["users"]
    assert "active" in data["users"]
    assert "banned" in data["users"]

    assert "content" in data
    assert "submissions" in data["content"]
    assert "shadow_sessions" in data["content"]
    assert "groups" in data["content"]

    assert "engagement" in data
    assert "avg_coins" in data["engagement"]
    assert "avg_streak" in data["engagement"]

    # Verify counts
    assert data["users"]["total"] >= 3  # admin + 2 regular users


def test_admin_only_access(client: TestClient, db):
    """Test that only admins can access admin endpoints."""
    # Create regular user
    user = create_regular_user(db, "regular@example.com")

    # Login as regular user
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "regular@example.com", "password": "user123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try to access admin stats
    r = client.get(f"{settings.API_V1_STR}/admin/stats", headers=headers)
    assert r.status_code == 403 or r.status_code == 401  # Should be forbidden


def test_list_all_users(client: TestClient, db):
    """Test listing all users with pagination."""
    # Create admin
    admin = create_admin_user(db, "admin2@example.com")

    # Create multiple regular users
    for i in range(15):
        create_regular_user(db, f"listuser{i}@example.com")

    # Login as admin
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin2@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get users list
    r = client.get(f"{settings.API_V1_STR}/admin/users", headers=headers)
    assert r.status_code == 200
    data = r.json()

    assert "total" in data
    assert "users" in data
    assert data["total"] >= 15
    assert isinstance(data["users"], list)

    # Test pagination
    r = client.get(f"{settings.API_V1_STR}/admin/users?skip=5&limit=5", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data["users"]) <= 5


def test_search_users(client: TestClient, db):
    """Test user search functionality."""
    # Create admin
    admin = create_admin_user(db, "admin3@example.com")

    # Create users with specific names
    user_in = UserCreate(
        email="john.doe@example.com", password="pass", full_name="John Doe"
    )
    crud_user.create(db, obj_in=user_in)

    user_in = UserCreate(
        email="jane.smith@example.com", password="pass", full_name="Jane Smith"
    )
    crud_user.create(db, obj_in=user_in)

    # Login as admin
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin3@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Search for "john"
    r = client.get(f"{settings.API_V1_STR}/admin/users?search=john", headers=headers)
    assert r.status_code == 200
    data = r.json()

    # Should find John Doe
    assert any(
        "john" in user["email"].lower() or "john" in (user["full_name"] or "").lower()
        for user in data["users"]
    )


def test_ban_user(client: TestClient, db):
    """Test banning a user."""
    # Create admin and user
    admin = create_admin_user(db, "admin4@example.com")
    user = create_regular_user(db, "toban@example.com")

    # Login as admin
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin4@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Ban the user
    r = client.put(f"{settings.API_V1_STR}/admin/users/{user.id}/ban", headers=headers)
    assert r.status_code == 200
    data = r.json()

    assert data["message"] == "User banned successfully"
    assert data["user"]["is_banned"] == True
    assert data["user"]["is_active"] == False

    # Verify admin log was created
    log = (
        db.query(AdminLog)
        .filter(AdminLog.action == "ban_user", AdminLog.target_id == user.id)
        .first()
    )
    assert log is not None
    assert log.admin_id == admin.id


def test_unban_user(client: TestClient, db):
    """Test unbanning a user."""
    # Create admin and banned user
    admin = create_admin_user(db, "admin5@example.com")
    user = create_regular_user(db, "banned@example.com")
    user.is_banned = True
    user.is_active = False
    db.commit()

    # Login as admin
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin5@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Unban the user
    r = client.put(
        f"{settings.API_V1_STR}/admin/users/{user.id}/unban", headers=headers
    )
    assert r.status_code == 200
    data = r.json()

    assert data["message"] == "User unbanned successfully"
    assert data["user"]["is_banned"] == False
    assert data["user"]["is_active"] == True


def test_promote_to_admin(client: TestClient, db):
    """Test promoting a user to admin."""
    # Create admin and user
    admin = create_admin_user(db, "admin6@example.com")
    user = create_regular_user(db, "topromote@example.com")

    # Login as admin
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin6@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Promote user
    r = client.put(
        f"{settings.API_V1_STR}/admin/users/{user.id}/promote", headers=headers
    )
    assert r.status_code == 200
    data = r.json()

    assert data["message"] == "User promoted to admin"
    assert data["user"]["role"] == "admin"

    # Verify admin log
    log = (
        db.query(AdminLog)
        .filter(AdminLog.action == "promote_user", AdminLog.target_id == user.id)
        .first()
    )
    assert log is not None


def test_delete_user(client: TestClient, db):
    """Test deleting a user (soft delete)."""
    # Create admin and user
    admin = create_admin_user(db, "admin7@example.com")
    user = create_regular_user(db, "todelete@example.com")

    # Login as admin
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin7@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Delete user
    r = client.delete(f"{settings.API_V1_STR}/admin/users/{user.id}", headers=headers)
    assert r.status_code == 200

    # Verify user is marked inactive
    db.refresh(user)
    assert user.is_active == False


def test_cannot_delete_admin(client: TestClient, db):
    """Test that admins cannot delete other admins."""
    # Create two admins
    admin1 = create_admin_user(db, "admin8@example.com")
    admin2 = create_admin_user(db, "admin9@example.com")

    # Login as admin1
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin8@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try to delete admin2
    r = client.delete(f"{settings.API_V1_STR}/admin/users/{admin2.id}", headers=headers)
    assert r.status_code == 403
    assert "Cannot delete admin users" in r.json()["detail"]


def test_get_user_details(client: TestClient, db):
    """Test getting detailed user information."""
    # Create admin and user with activity
    admin = create_admin_user(db, "admin10@example.com")
    user = create_regular_user(db, "detailed@example.com")

    # Add some user activity
    submission = HandwritingSubmission(
        user_id=user.id, image_url="test.jpg", report_content="test"
    )
    db.add(submission)

    session = ShadowModeSession(
        user_id=user.id, day_number=1, total_goals=3, is_active=False
    )
    db.add(session)
    db.commit()

    # Login as admin
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin10@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user details
    r = client.get(f"{settings.API_V1_STR}/admin/users/{user.id}", headers=headers)
    assert r.status_code == 200
    data = r.json()

    assert "user" in data
    assert "statistics" in data
    assert data["statistics"]["submissions"] == 1
    assert data["statistics"]["shadow_sessions"] == 1


def test_admin_logs(client: TestClient, db):
    """Test retrieving admin activity logs."""
    # Create admin
    admin = create_admin_user(db, "admin11@example.com")
    user = create_regular_user(db, "logtest@example.com")

    # Login as admin
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin11@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Perform some admin actions
    client.put(f"{settings.API_V1_STR}/admin/users/{user.id}/ban", headers=headers)
    client.put(f"{settings.API_V1_STR}/admin/users/{user.id}/unban", headers=headers)

    # Get logs
    r = client.get(f"{settings.API_V1_STR}/admin/logs", headers=headers)
    assert r.status_code == 200
    data = r.json()

    assert "logs" in data
    assert isinstance(data["logs"], list)
    assert len(data["logs"]) >= 2

    # Verify log structure
    for log in data["logs"]:
        assert "admin_id" in log
        assert "action" in log
        assert "target_type" in log
        assert "target_id" in log


def test_filter_users_by_role(client: TestClient, db):
    """Test filtering users by role."""
    # Create admin and users
    admin = create_admin_user(db, "admin12@example.com")
    create_regular_user(db, "roletest1@example.com")

    another_admin_in = UserCreate(
        email="roletest2@example.com", password="pass", full_name="Test Admin"
    )
    another_admin = crud_user.create(db, obj_in=another_admin_in)
    another_admin.role = "admin"
    db.commit()

    # Login as admin
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin12@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Filter by admin role
    r = client.get(f"{settings.API_V1_STR}/admin/users?role=admin", headers=headers)
    assert r.status_code == 200
    data = r.json()

    # All returned users should be admins
    for user in data["users"]:
        assert user["role"] == "admin"


def test_filter_banned_users(client: TestClient, db):
    """Test filtering banned users."""
    # Create admin
    admin = create_admin_user(db, "admin13@example.com")

    # Create banned and active users
    banned_user = create_regular_user(db, "banned1@example.com")
    banned_user.is_banned = True
    db.commit()

    create_regular_user(db, "active1@example.com")

    # Login as admin
    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin13@example.com", "password": "admin123"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Filter banned users
    r = client.get(f"{settings.API_V1_STR}/admin/users?is_banned=true", headers=headers)
    assert r.status_code == 200
    data = r.json()

    # All returned users should be banned
    for user in data["users"]:
        assert user["is_banned"] == True


def test_unauthorized_admin_access(client: TestClient, db):
    """Test that admin endpoints require authentication."""
    # Try to access without token
    r = client.get(f"{settings.API_V1_STR}/admin/stats")
    assert r.status_code == 401

    r = client.get(f"{settings.API_V1_STR}/admin/users")
    assert r.status_code == 401

    r = client.get(f"{settings.API_V1_STR}/admin/logs")
    assert r.status_code == 401
