import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "ktej255@gmail.com"

def test_password_recovery():
    print(f"Testing password recovery for {EMAIL}...")
    url = f"{BASE_URL}/login/password-recovery"
    print(f"POST {url}")
    
    try:
        response = requests.post(url, json={"email": EMAIL})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_password_recovery()
