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

    # Required fields
    assert "status" in data
    assert "timestamp" in data
    assert "environment" in data
    assert "checks" in data

    # Status should be one of the expected values
    assert data["status"] in ["healthy", "degraded", "unhealthy"]

    # Timestamp should be a number
    assert isinstance(data["timestamp"], (int, float))

    # Environment should be a string
    assert isinstance(data["environment"], str)

    # Checks should be a dict
    assert isinstance(data["checks"], dict)


def test_health_database_check(client):
    """Test that the database check is present"""
    response = client.get("/health")
    data = response.json()

    assert "database" in data["checks"]
    assert "status" in data["checks"]["database"]
    assert "message" in data["checks"]["database"]

    # Database should be healthy in test environment
    assert data["checks"]["database"]["status"] == "healthy"


def test_health_cache_check(client):
    """Test that the cache check is present"""
    response = client.get("/health")
    data = response.json()

    assert "cache" in data["checks"]
    assert "status" in data["checks"]["cache"]
    assert "message" in data["checks"]["cache"]

    # Cache status should be either healthy or degraded (since it's optional)
    assert data["checks"]["cache"]["status"] in ["healthy", "degraded"]


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
