from fastapi.testclient import TestClient
from app.core.config import settings
from app import models
from app.schemas.user import UserCreate
from app.crud import user as crud_user

def create_user(db, email="emailtest@example.com"):
    user_in = UserCreate(email=email, password="password", full_name="Email Test User")
    user = crud_user.create(db, obj_in=user_in)
    return user

def get_auth_headers(client, email="emailtest@example.com"):
    login_resp = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": "password"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_email_preferences(client: TestClient, db):
    user = create_user(db)
    headers = get_auth_headers(client, user.email)
    
    resp = client.get(
        f"{settings.API_V1_STR}/email-notifications/preferences",
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "user_id" in data
    assert data["user_id"] == user.id

def test_update_email_preferences(client: TestClient, db):
    # Assumes user created in previous test or new user
    # Better to create new user to avoid conflicts if DB not reset
    user = create_user(db, "emailupdate@example.com")
    headers = get_auth_headers(client, user.email)
    
    update_data = {"general_enabled": False}
    resp = client.patch(
        f"{settings.API_V1_STR}/email-notifications/preferences",
        headers=headers,
        json=update_data
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["general_enabled"] == False

def test_get_email_templates(client: TestClient, db):
    user = create_user(db, "emailtemplates@example.com")
    headers = get_auth_headers(client, user.email)
    
    resp = client.get(
        f"{settings.API_V1_STR}/email-notifications/templates",
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
