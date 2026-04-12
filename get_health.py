import sys
import os

sys.path.insert(0, '/app')

from unittest.mock import MagicMock
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["google.generativeai.types"] = MagicMock()

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
response = client.get("/health")
print("Response:", response.json())
