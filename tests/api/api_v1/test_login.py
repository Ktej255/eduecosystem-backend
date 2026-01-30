from typing import Dict
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.utils import random_email, random_lower_string
from app.core.security import get_password_hash
from app.models.user import User

def test_get_access_token(client: TestClient, normal_user) -> None:
    login_data = {
        "username": "normal_user@example.com",
        "password": "testpassword",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]

def test_use_access_token(client: TestClient, normal_user_token_headers: Dict[str, str]) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result
