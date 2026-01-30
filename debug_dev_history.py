import sys
import os
# Add backend to path
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from main import app
from app.core.config import settings
from app.models.user import User
from app.api.api_v1.endpoints.development_history import check_admin

# Mock admin user
mock_admin = User(id=1, email="admin@test.com", role="admin", is_superuser=True)

# Override auth dependency
app.dependency_overrides[check_admin] = lambda: mock_admin

client = TestClient(app)

print("Sending request...")
response = client.post(
    f"{settings.API_V1_STR}/admin/ai-planning/generate",
    json={"days_to_analyze": 7}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
