from fastapi.testclient import TestClient


def test_simple(client: TestClient):
    """Simple test to verify test infrastructure works"""
    response = client.get("/health")
    assert response.status_code == 200
