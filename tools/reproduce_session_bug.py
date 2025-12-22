import requests
import sys
import uuid

API_URL = "http://localhost:8007/api/v1"
EMAIL = f"session_bug_{uuid.uuid4()}@example.com"
PASSWORD = "password123"

def reproduce_bug():
    print(f"Attempting to register user: {EMAIL}")
    try:
        response = requests.post(
            f"{API_URL}/login/register",
            json={
                "email": EMAIL,
                "password": PASSWORD,
                "full_name": "Session Bug User",
                "role": "student"
            }
        )
        
        if response.status_code != 200:
            print(f"Registration failed: {response.status_code} - {response.text}")
            sys.exit(1)
            
        data = response.json()
        print("Registration successful.")
        print(f"Response keys: {list(data.keys())}")
        
        if "access_token" in data:
            print("SUCCESS: Access token found in registration response.")
            sys.exit(0)
        else:
            print("FAILURE: Access token NOT found in registration response.")
            print("User cannot auto-login.")
            sys.exit(1)

    except Exception as e:
        print(f"Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reproduce_bug()
