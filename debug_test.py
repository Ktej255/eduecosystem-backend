import sys
import os
# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from tests.api.api_v1.test_learning_groups_integration import test_create_learning_group
from fastapi.testclient import TestClient
from main import app

db = SessionLocal()
client = TestClient(app)
try:
    print("Running test_create_learning_group...")
    test_create_learning_group(client, db)
    print("Success")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
