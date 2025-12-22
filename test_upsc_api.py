
import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "ktej255@gmail.com"
PASSWORD = "Admin@123"

def test_api():
    # 1. Login
    print("Logging in...")
    try:
        response = requests.post(f"{BASE_URL}/login/access-token", data={
            "username": EMAIL,
            "password": PASSWORD
        })
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")
        
        # 2. Get Student Dashboard
        print("\nTesting GET /upsc/student/dashboard...")
        response = requests.get(f"{BASE_URL}/upsc/student/dashboard", headers=headers)
        if response.status_code == 200:
            print("Success!")
            print(response.json())
        else:
            print(f"Failed: {response.status_code} - {response.text}")

        # 3. Get Student Plans
        print("\nTesting GET /upsc/student/plans...")
        response = requests.get(f"{BASE_URL}/upsc/student/plans", headers=headers)
        if response.status_code == 200:
            print("Success!")
            plans = response.json()
            print(f"Found {len(plans)} plans.")
            if plans:
                plan_id = plans[0]["id"]
                
                # 4. Get Plan Status
                print(f"\nTesting GET /upsc/student/plans/{plan_id}/status...")
                response = requests.get(f"{BASE_URL}/upsc/student/plans/{plan_id}/status", headers=headers)
                if response.status_code == 200:
                    print("Success!")
                    print(response.json())
                else:
                    print(f"Failed: {response.status_code} - {response.text}")
        else:
            print(f"Failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
