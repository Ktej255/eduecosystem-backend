from fastapi.testclient import TestClient
from app.core.config import settings
from app.crud import user as crud_user
from app.schemas.user import UserCreate


def test_upload_handwriting(client: TestClient, db):
    # Create user and login
    email = "grapho@example.com"
    password = "password"
    user_in = UserCreate(email=email, password=password, full_name="Grapho User")
    user = crud_user.create(db, obj_in=user_in)

    # Login to get token
    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Create a dummy file
    # We need to make sure the backend can save it.
    # The backend saves to "uploads/{user_id}_{filename}"
    files = {"file": ("test.jpg", b"fake image content", "image/jpeg")}

    r = client.post(
        f"{settings.API_V1_STR}/grapho/upload", headers=headers, files=files
    )
    assert r.status_code == 200
    data = r.json()
    assert "submission_id" in data
    assert "extracted_text" in data
    assert data["coins_earned"] == 50
