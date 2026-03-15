
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/api_v1"

# Note: You need a valid JWT token to run this. 
# For reproduction/testing, we assume a local dev server is running with an admin user.
TOKEN = "YOUR_JWT_TOKEN_HERE" 

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_meditation_purchase():
    print("\n--- Testing Meditation Purchase Initiation ---")
    payload = {"level": 2}
    response = requests.post(f"{BASE_URL}/meditation/level/2/purchase/initiate", headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_graphotherapy_purchase():
    print("\n--- Testing Graphotherapy Purchase Initiation ---")
    payload = {"level_id": 2, "is_bundle": False, "use_coins": True}
    response = requests.post(f"{BASE_URL}/graphotherapy/purchase/initiate", headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

if __name__ == "__main__":
    print("Reproduction Script for Cashfree Integration")
    # Uncomment to run if server is up and token is valid
    # test_meditation_purchase()
    # test_graphotherapy_purchase()
