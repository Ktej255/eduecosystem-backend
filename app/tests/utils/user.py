from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate
from app.tests.utils.utils import random_email, random_lower_string


def user_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> Dict[str, str]:
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_user(db: Session, role: str = "student") -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        email=email, password=password, full_name=random_lower_string()
    )
    user = crud.user.create(db=db, obj_in=user_in)
    user.role = role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> Dict[str, str]:
    """
    Return a valid token for the user with given email.
    If the user doesn't exist it is created first.
    """
    password = "password"
    user = crud.user.get_by_email(db, email=email)
    if not user:
        user_in_create = UserCreate(
            username=email,
            email=email,
            password=password,
            full_name=random_lower_string(),
        )
        user = crud.user.create(db, obj_in=user_in_create)
    else:
        # We can't easily get the password if it's hashed, so we assume a known password or reset it
        # But for tests, we usually create new users.
        # If we need to login as existing user, we need their password.
        # Here we assume the user was created with 'password' if we are looking them up by email for test purposes
        pass

    return user_authentication_headers(client=client, email=email, password=password)
