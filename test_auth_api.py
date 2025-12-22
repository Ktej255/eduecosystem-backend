import requests
import json
import random
import string

BASE_URL = "http://localhost:8000/api/v1"

def generate_random_email():
    return f"student_{''.join(random.choices(string.ascii_lowercase, k=8))}@example.com"

def test_signup():
    email = generate_random_email()
    password = "Student@123"
    full_name = "Test Student"
    
    print(f"Testing signup with: {email}")
    
    try:
        response = requests.post(f"{BASE_URL}/login/register", json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "username": email.split('@')[0]
        })
        
        if response.status_code == 200:
            print("✅ Signup successful!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Signup failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_admin_login():
    email = "ktej255@gmail.com"
    password = "Tej@1106"
    
    print(f"\nTesting admin login with: {email}")
    
    try:
        response = requests.post(f"{BASE_URL}/login/access-token", data={
            "username": email,
            "password": password
        })
        
        if response.status_code == 200:
            print("✅ Admin login successful!")
            return True
        else:
            print(f"❌ Admin login failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("--- Starting Auth Tests ---")
    signup_success = test_signup()
    login_success = test_admin_login()
    
    if signup_success and login_success:
        print("\n🎉 ALL AUTH TESTS PASSED")
    else:
        print("\n⚠️ SOME TESTS FAILED")
