#!/usr/bin/env python3
"""
Health Check Test Script
Tests the /health endpoint functionality
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from main import app


def test_health_endpoint():
    """Test the health check endpoint"""
    client = TestClient(app)

    print("=" * 60)
    print("Testing Health Check Endpoint")
    print("=" * 60)

    # Test health endpoint
    response = client.get("/health")

    print(f"\n✅ Status Code: {response.status_code}")
    print("\n📋 Response:")

    import json

    health_data = response.json()
    print(json.dumps(health_data, indent=2))

    # Verify response structure
    print("\n🔍 Verifications:")
    checks = []

    if "status" in health_data:
        print(f"  ✅ Status field present: {health_data['status']}")
        checks.append(True)
    else:
        print("  ❌ Status field missing")
        checks.append(False)

    if "timestamp" in health_data:
        print(f"  ✅ Timestamp field present: {health_data['timestamp']}")
        checks.append(True)
    else:
        print("  ❌ Timestamp field missing")
        checks.append(False)

    if "environment" in health_data:
        print(f"  ✅ Environment field present: {health_data['environment']}")
        checks.append(True)
    else:
        print("  ❌ Environment field missing")
        checks.append(False)

    if "checks" in health_data:
        print("  ✅ Checks field present")

        # Check database status
        if "database" in health_data["checks"]:
            db_status = health_data["checks"]["database"]["status"]
            print(f"    ✅ Database check: {db_status}")
            checks.append(True)
        else:
            print("    ❌ Database check missing")
            checks.append(False)

        # Check cache status
        if "cache" in health_data["checks"]:
            cache_status = health_data["checks"]["cache"]["status"]
            print(f"    ✅ Cache check: {cache_status}")
            checks.append(True)
        else:
            print("    ❌ Cache check missing")
            checks.append(False)
    else:
        print("  ❌ Checks field missing")
        checks.append(False)

    # Summary
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ ALL HEALTH CHECK TESTS PASSED!")
    else:
        print("❌ SOME HEALTH CHECK TESTS FAILED")
    print("=" * 60)

    return all(checks)


def test_config():
    """Test configuration settings"""
    from app.core.config import settings

    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)

    print("\n📋 Configuration:")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Database URL: {settings.DATABASE_URL}")
    print(f"  SECRET_KEY length: {len(settings.SECRET_KEY)} characters")
    print(f"  Project Name: {settings.PROJECT_NAME}")

    # Verify SECRET_KEY
    if len(settings.SECRET_KEY) >= 32:
        print("\n  ✅ SECRET_KEY meets minimum length requirement (32+ chars)")
    else:
        print("\n  ⚠️  SECRET_KEY is short (development mode)")

    print("=" * 60)


if __name__ == "__main__":
    try:
        # Test configuration first
        test_config()

        # Test health endpoint
        test_health_endpoint()

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
