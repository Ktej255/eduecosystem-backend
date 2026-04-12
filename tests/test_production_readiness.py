"""
Test health check endpoint and production readiness features
"""

import pytest


def test_health_endpoint_exists(client):
    """Test that the health endpoint exists and returns 200"""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_structure(client):
    """Test that the health endpoint has the expected structure"""
    response = client.get("/health")
    data = response.json()

    # Required fields based on the new endpoint structure
    assert "status" in data
    assert "message" in data
    assert "version" in data

    # Status should be ok
    assert data["status"] == "ok"
    assert data["message"] == "Backend is healthy"


def test_config_secret_key_exists():
    """Test that SECRET_KEY is configured"""
    from app.core.config import settings

    assert settings.SECRET_KEY is not None
    assert len(settings.SECRET_KEY) > 0


def test_config_secret_key_length():
    """Test that SECRET_KEY meets minimum length requirement in non-dev environments"""
    from app.core.config import settings

    # In development, key can be auto-generated
    # In production, it must be at least 32 characters
    if settings.ENVIRONMENT == "production":
        assert len(settings.SECRET_KEY) >= 32, (
            "SECRET_KEY must be at least 32 characters in production"
        )
    else:
        # In development, we still generate a secure key
        assert len(settings.SECRET_KEY) > 0


def test_config_environment_variable():
    """Test that ENVIRONMENT variable is set"""
    from app.core.config import settings

    assert settings.ENVIRONMENT in ["development", "staging", "production"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
