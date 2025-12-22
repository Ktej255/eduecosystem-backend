from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_ai_tutor_chat_unauthorized():
    """Test that unauthenticated users cannot access AI tutor"""
    response = client.post(
        "/api/v1/tutor/chat", json={"message": "Hello, can you help me?"}
    )
    assert response.status_code == 401


def test_ai_tutor_explain_unauthorized():
    """Test that explain endpoint requires authentication"""
    response = client.post("/api/v1/tutor/explain", json={"concept": "recursion"})
    assert response.status_code == 401


def test_ai_tutor_history_unauthorized():
    """Test that history endpoint requires authentication"""
    response = client.get("/api/v1/tutor/history")
    assert response.status_code == 401


# Note: Authenticated tests require mocking or test user creation
# These would be added with proper test fixtures
