"""
Integration Tests Example
Tests API endpoints with database
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.db.session import Base
from app.api import deps
from app.models.user import User
from app.core.security import get_password_hash

from sqlalchemy.pool import StaticPool

# Test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Create test client"""

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[deps.get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True,
        role="instructor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers"""
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "test@example.com", "password": "testpassword"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# TESTS
# ============================================================================


def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client, test_user):
    """Test login with wrong password"""
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 400


def test_get_current_user(client, auth_headers, test_user):
    """Test getting current user info"""
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_create_course(client, auth_headers, db):
    """Test course creation"""
    response = client.post(
        "/api/v1/courses/",
        headers=auth_headers,
        json={
            "title": "Test Course",
            "description": "A test course",
            "price": 999,
            "level": "beginner",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Course"


def test_enroll_in_course(client, auth_headers, db):
    """Test course enrollment"""
    # First create a course
    course_response = client.post(
        "/api/v1/courses/",
        headers=auth_headers,
        json={
            "title": "Test Course",
            "description": "A test course",
            "price": 0,  # Free course
            "level": "beginner",
            "is_published": True,
        },
    )
    course_id = course_response.json()["id"]

    # Then enroll
    enroll_response = client.post(
        f"/api/v1/courses/{course_id}/enroll", headers=auth_headers
    )
    assert enroll_response.status_code == 201


def test_gamification_coins(client, auth_headers, db):
    """Test coin transactions"""
    response = client.get("/api/v1/gamification/transactions", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_achievements_list(client, auth_headers):
    """Test listing achievements"""
    response = client.get("/api/v1/achievements", headers=auth_headers)
    assert response.status_code == 200


def test_learning_groups_list(client, auth_headers):
    """Test listing learning groups"""
    response = client.get("/api/v1/learning-groups/groups", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
