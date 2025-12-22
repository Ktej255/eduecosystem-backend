from fastapi.testclient import TestClient
from app.core.config import settings
from app.crud import user as crud_user
from app.schemas.user import UserCreate


def test_signup(client: TestClient, db):
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        json={
            "email": "signup@example.com",
            "password": "password123",
            "full_name": "Signup User",
        },
    )
    assert r.status_code == 200
    new_user = r.json()
    assert new_user["email"] == "signup@example.com"
    assert "id" in new_user


def test_login_access_token(client: TestClient, db):
    email = "login@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password, full_name="Login User")
    crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"
