import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "ktej255@gmail.com"  # Using the email from the screenshot

def test_password_recovery():
    print(f"Testing password recovery for {EMAIL}...")
    url = f"{BASE_URL}/login/password-recovery/{EMAIL}"
    print(f"POST {url}")
    
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_password_recovery()
