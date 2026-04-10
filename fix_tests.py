import sys
import os

sys.path.insert(0, '/app')

from unittest.mock import MagicMock
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["google.generativeai.types"] = MagicMock()

sys.modules["pytest"] = MagicMock()

def run_tests():
    from main import app
    from fastapi.testclient import TestClient
    from tests import test_production_readiness

    client = TestClient(app)

    print("Running test_health_endpoint_exists...")
    test_production_readiness.test_health_endpoint_exists(client)

    print("Running test_health_endpoint_structure...")
    test_production_readiness.test_health_endpoint_structure(client)

    print("Running config checks...")
    test_production_readiness.test_config_secret_key_exists()
    test_production_readiness.test_config_secret_key_length()
    test_production_readiness.test_config_environment_variable()

    print("All tests passed!")

if __name__ == "__main__":
    run_tests()
