from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.development_history import DevelopmentLog, DailyDevReport
import pytest
from datetime import date, timedelta
from app.models.user import User
from app.core import security

@pytest.fixture
def superuser_token_headers(client: TestClient, db: Session) -> dict:
    from app.db.base import Base
    print(f"DEBUG: Registered tables in metadata: {list(Base.metadata.tables.keys())}")
    
    email = "superuser_dev_history@example.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=security.get_password_hash("password"),
            full_name="Super User Dev History",
            is_active=True,
            is_superuser=True,
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    print(f"DEBUG: Superuser created/found: {user.id}, {user.email}")
    check_user = db.query(User).filter(User.id == user.id).first()
    print(f"DEBUG: Check user in DB: {check_user}")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    return {"Authorization": f"Bearer {token}"}

def test_create_development_log(
    client: TestClient, superuser_token_headers: dict, db: Session
):
    data = {
        "date": str(date.today()),
        "title": "Test Log",
        "description": "Testing the API",
        "batch": "Test Batch",
        "features": ["Feat 1", "Feat 2"],
        "challenges": ["Challenge 1"]
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/development-logs",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["log"]["title"] == "Test Log"
    assert "id" in content["log"]

def test_get_development_logs(
    client: TestClient, superuser_token_headers: dict, db: Session
):
    response = client.get(
        f"{settings.API_V1_STR}/admin/development-logs",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "logs" in content
    assert content["total"] >= 0

def test_auto_generate_daily_report(
    client: TestClient, superuser_token_headers: dict, db: Session
):
    # First ensure a log exists for today (created in test_create_development_log)
    response = client.post(
        f"{settings.API_V1_STR}/admin/daily-reports/auto-generate",
        headers=superuser_token_headers,
    )
    # Should work, either created or already exists
    assert response.status_code == 200
    content = response.json()
    assert "message" in content

def test_get_pdr_graph(
    client: TestClient, superuser_token_headers: dict
):
    response = client.get(
        f"{settings.API_V1_STR}/admin/pdr/graph",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "nodes" in content
    assert "links" in content
    assert len(content["nodes"]) > 0

def test_get_ai_plan(
    client: TestClient, superuser_token_headers: dict
):
    # This calls external API, might be slow or fail if no key.
    # We'll just check if endpoint is reachable and handles missing key gracefully
    # or simple mock if possible. For now just checking it requires auth
    response = client.post(
        f"{settings.API_V1_STR}/admin/ai-planning/generate",
        headers=superuser_token_headers,
        json={"days_to_analyze": 7}
    )

    # It might return 200 with plan or 500 if key missing, but we expect at least parsing
    # Since we implemented try-except block in endpoint, it should return 200 with fallback
    assert response.status_code == 200
    content = response.json()
    assert "plan_items" in content
