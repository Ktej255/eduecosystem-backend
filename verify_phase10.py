
import os
import sys
from fastapi.testclient import TestClient

# Add root directory to path
sys.path.append(os.getcwd())

from backend.app.main import app
from backend.app.api.deps import get_current_user
from backend.app.models.user import User

# Define logic to mock authentication
def override_get_current_user():
    # Return a dummy user object that mimics the SQLAlchemy model
    class MockUser:
        id = 1
        email = "test@example.com"
        full_name = "Test User"
        hashed_password = "fake"
        is_active = True
        is_superuser = False
    return MockUser()

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_generate_mcq():
    print("Testing generate-mcq...")
    response = client.post("/api/v1/ai-learning/generate-mcq", json={
        "notes_text": "The Mughal Empire was founded by Babur in 1526. Humayun succeeded him. Akbar was the greatest Mughal emperor.",
        "num_questions": 2,
        "difficulty": "easy"
    })
    
    if response.status_code != 200:
        print(f"FAILED: {response.text}")
        return False
        
    data = response.json()
    print(f"Response keys: {data.keys()}")
    if "questions" in data and len(data["questions"]) > 0:
        print("SUCCESS: MCQs generated.")
        return True
    return False

def test_coaching_flow():
    print("\nTesting Coaching Flow...")
    
    # 1. Start Session
    print("1. Start Session")
    resp1 = client.post("/api/v1/ai-learning/start-coaching", json={
        "topic": "Mughal History",
        "context_data": {"level": "beginner"}
    })
    if resp1.status_code != 200:
        print(f"Start Failed: {resp1.text}")
        return False
    
    data1 = resp1.json()
    session_id = data1.get("session_id")
    print(f"Session ID: {session_id}")
    print(f"Coach Greeting: {data1.get('message')}")
    
    if not session_id:
        return False

    # 2. Chat
    print("2. Chat with Coach")
    resp2 = client.post("/api/v1/ai-learning/chat-with-coach", json={
        "session_id": session_id,
        "message": "Who was Akbar?"
    })
    if resp2.status_code != 200:
        print(f"Chat Failed: {resp2.text}")
        return False

    data2 = resp2.json()
    print(f"Coach Reply: {data2.get('message')}")
    print("SUCCESS: Coaching flow working.")
    return True

if __name__ == "__main__":
    if test_generate_mcq() and test_coaching_flow():
        print("\n=== ALL TESTS PASSED ===")
    else:
        print("\n=== SOME TESTS FAILED ===")
        sys.exit(1)
