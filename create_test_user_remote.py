
import requests
import sys

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

def register_user():
    print("Registering test user...")
    try:
        # Check if email exists first? API will return 400 if so, which is fine.
        resp = requests.post(f"{API_V1}/users/", json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        })
        if resp.status_code == 200:
            print("Registration SUCCESS")
            return True
        elif resp.status_code == 400 and "already exists" in resp.text:
            print("User already exists. Proceeding.")
            return True
        else:
            print(f"Registration FAILED: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"Connection Error: {e}")
        return False

if __name__ == "__main__":
    if register_user():
        sys.exit(0)
    else:
        sys.exit(1)
