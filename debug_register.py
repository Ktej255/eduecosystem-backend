from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_debug_register():
    response = client.post(
        "/api/v1/login/register",
        json={
            "email": "debug_reg@test.com",
            "password": "password123",
            "full_name": "Debug Register",
            "role": "student"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Also check access-token to be sure
    print("Checking access-token route...")
    resp_login = client.post("/api/v1/login/access-token", data={"username": "x", "password": "x"})
    print(f"Login Status: {resp_login.status_code}") # Should be 400 or 404
