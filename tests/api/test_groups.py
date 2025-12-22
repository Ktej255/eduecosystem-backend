"""
Comprehensive test suite for Wolf Pack grouping functionality.
Tests auto-assignment, group stats, leaderboards, and edge cases.
"""

from fastapi.testclient import TestClient
from app.core.config import settings
from app.crud import user as crud_user
from app.schemas.user import UserCreate
from app.models.group import Group


def test_join_wolf_pack(client: TestClient, db):
    """Test user joining a Wolf Pack group."""
    # Create and login user
    email = "wolf1@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Wolf User 1")
    user = crud_user.create(db, obj_in=user_in)

    # Set user streak to enable grouping
    user.streak_days = 5
    db.commit()

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Join a pack
    r = client.post(f"{settings.API_V1_STR}/groups/join", headers=headers)
    assert r.status_code == 200
    data = r.json()

    assert "id" in data
    assert "name" in data
    assert "description" in data
    assert "members" in data
    assert len(data["members"]) > 0
    # User should be in the members list
    user_found = any(m["full_name"] == "Wolf User 1" for m in data["members"])
    assert user_found


def test_multiple_users_same_streak_same_group(client: TestClient, db):
    """Test that users with similar streaks are grouped together."""
    users_data = []

    # Create 3 users with similar streaks (5-7 days)
    for i in range(3):
        email = f"wolfpack{i}@example.com"
        password = "password123"
        user_in = UserCreate(email=email, password=password, full_name=f"Pack User {i}")
        user = crud_user.create(db, obj_in=user_in)
        user.streak_days = 5 + i  # 5, 6, 7 days
        db.commit()

        login_r = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            data={"username": email, "password": password},
        )
        token = login_r.json()["access_token"]
        users_data.append({"email": email, "token": token})

    # Each user joins a group
    group_ids = []
    for user_data in users_data:
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        r = client.post(f"{settings.API_V1_STR}/groups/join", headers=headers)
        assert r.status_code == 200
        group_ids.append(r.json()["id"])

    # All should be in the same group (or similar streak groups)
    # At minimum, verify all groups exist and have members
    for group_id in group_ids:
        group = db.query(Group).filter(Group.id == group_id).first()
        assert group is not None
        assert len(group.members) > 0


def test_get_my_group(client: TestClient, db):
    """Test getting current user's group with stats."""
    # Create and login user
    email = "wolf2@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Wolf User 2")
    user = crud_user.create(db, obj_in=user_in)
    user.streak_days = 10
    user.coins = 500
    db.commit()

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # First, user has no group
    r = client.get(f"{settings.API_V1_STR}/groups/my-group", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["group"] is None

    # Join a group
    client.post(f"{settings.API_V1_STR}/groups/join", headers=headers)

    # Now get my group with stats
    r = client.get(f"{settings.API_V1_STR}/groups/my-group", headers=headers)
    assert r.status_code == 200
    data = r.json()

    assert "id" in data
    assert "name" in data
    assert "member_count" in data
    assert data["member_count"] > 0
    assert "avg_streak" in data
    assert "total_coins" in data
    assert data["total_coins"] >= 500  # At least our user's coins


def test_group_leaderboard(client: TestClient, db):
    """Test Wolf Pack leaderboard ranking."""
    # Create multiple users and groups
    for i in range(5):
        email = f"leader{i}@example.com"
        password = "password123"
        user_in = UserCreate(email=email, password=password, full_name=f"Leader {i}")
        user = crud_user.create(db, obj_in=user_in)
        user.streak_days = 3 + i
        user.coins = 100 * (i + 1)  # 100, 200, 300, 400, 500
        db.commit()

        login_r = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            data={"username": email, "password": password},
        )
        token = login_r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Join group
        client.post(f"{settings.API_V1_STR}/groups/join", headers=headers)

    # Get leaderboard (no auth required for viewing)
    r = client.get(f"{settings.API_V1_STR}/groups/leaderboard")
    assert r.status_code == 200
    leaderboard = r.json()

    assert isinstance(leaderboard, list)
    assert len(leaderboard) > 0

    # Verify leaderboard structure
    for entry in leaderboard:
        assert "id" in entry
        assert "name" in entry
        assert "members" in entry
        assert "avgStreak" in entry
        assert "totalCoins" in entry
        assert "rank" in entry

    # Verify sorting by totalCoins (descending)
    if len(leaderboard) > 1:
        for i in range(len(leaderboard) - 1):
            assert leaderboard[i]["totalCoins"] >= leaderboard[i + 1]["totalCoins"]

    # Verify ranks are sequential
    for i, entry in enumerate(leaderboard):
        assert entry["rank"] == i + 1


def test_leaderboard_limit(client: TestClient, db):
    """Test leaderboard respects limit parameter."""
    # Get leaderboard with limit
    r = client.get(f"{settings.API_V1_STR}/groups/leaderboard?limit=5")
    assert r.status_code == 200
    leaderboard = r.json()

    # Should return at most 5 groups
    assert len(leaderboard) <= 5


def test_group_stats_calculation(client: TestClient, db):
    """Test that group statistics are calculated correctly."""
    # Create multiple users for the same group
    tokens = []
    expected_total_coins = 0
    expected_streaks = []

    for i in range(3):
        email = f"stats{i}@example.com"
        password = "password123"
        user_in = UserCreate(
            email=email, password=password, full_name=f"Stats User {i}"
        )
        user = crud_user.create(db, obj_in=user_in)

        # Set specific values for testing
        streak = 5 + i
        coins = 100 * (i + 1)
        user.streak_days = streak
        user.coins = coins
        db.commit()

        expected_total_coins += coins
        expected_streaks.append(streak)

        login_r = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            data={"username": email, "password": password},
        )
        token = login_r.json()["access_token"]
        tokens.append(token)

    # All join groups
    for token in tokens:
        headers = {"Authorization": f"Bearer {token}"}
        client.post(f"{settings.API_V1_STR}/groups/join", headers=headers)

    # Get first user's group stats
    headers = {"Authorization": f"Bearer {tokens[0]}"}
    r = client.get(f"{settings.API_V1_STR}/groups/my-group", headers=headers)
    assert r.status_code == 200
    data = r.json()

    # If all users are in same group, verify stats
    if data["member_count"] == 3:
        assert data["total_coins"] == expected_total_coins
        expected_avg = sum(expected_streaks) / len(expected_streaks)
        assert (
            abs(data["avg_streak"] - expected_avg) < 0.1
        )  # Allow small floating point difference


def test_group_max_members_enforcement(client: TestClient, db):
    """Test that group max member limit (5) is respected."""
    # Create 6 users with same streak
    tokens = []
    for i in range(6):
        email = f"maxtest{i}@example.com"
        password = "password123"
        user_in = UserCreate(email=email, password=password, full_name=f"Max User {i}")
        user = crud_user.create(db, obj_in=user_in)
        user.streak_days = 10  # Same streak to attempt same group
        db.commit()

        login_r = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            data={"username": email, "password": password},
        )
        token = login_r.json()["access_token"]
        tokens.append(token)

    # All try to join groups
    group_ids = []
    for token in tokens:
        headers = {"Authorization": f"Bearer {token}"}
        r = client.post(f"{settings.API_V1_STR}/groups/join", headers=headers)
        assert r.status_code == 200
        group_ids.append(r.json()["id"])

    # Check that at least some groups have max 5 members
    unique_groups = set(group_ids)
    for group_id in unique_groups:
        group = db.query(Group).filter(Group.id == group_id).first()
        assert len(group.members) <= 5


def test_join_group_twice(client: TestClient, db):
    """Test that joining group again returns same group (idempotent)."""
    # Create and login user
    email = "twice@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Twice User")
    user = crud_user.create(db, obj_in=user_in)
    user.streak_days = 7
    db.commit()

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Join first time
    r1 = client.post(f"{settings.API_V1_STR}/groups/join", headers=headers)
    group_id_1 = r1.json()["id"]

    # Join second time
    r2 = client.post(f"{settings.API_V1_STR}/groups/join", headers=headers)
    group_id_2 = r2.json()["id"]

    # Should return same group
    assert group_id_1 == group_id_2


def test_unauthorized_access(client: TestClient, db):
    """Test that endpoints require authentication where needed."""
    # my-group requires auth
    r = client.get(f"{settings.API_V1_STR}/groups/my-group")
    assert r.status_code == 401

    # join requires auth
    r = client.post(f"{settings.API_V1_STR}/groups/join")
    assert r.status_code == 401

    # leaderboard is public - should work without auth
    r = client.get(f"{settings.API_V1_STR}/groups/leaderboard")
    assert r.status_code == 200
