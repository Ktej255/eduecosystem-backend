import httpx
import time
import json

# Use production API for testing (local SQLite has schema issues)
BASE_URL = "https://cbdzkgkpmh.us-east-1.awsapprunner.com/api/v1"
EMAIL = "ktej255@gmail.com"
PASSWORD = "Tej@1106"

def verify_flow():
    with httpx.Client() as client:
        # 1. Login
        print("Logging in...")
        login_data = {
            "username": EMAIL,
            "password": PASSWORD
        }
        r = client.post(f"{BASE_URL}/login/access-token", data=login_data)
        if r.status_code != 200:
            print(f"Login failed: {r.text}")
            return
        
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Submit Study Cycle
        print("Submitting study cycle...")
        cycle_payload = {
            "topic_id": 102, # Fundamental Rights
            "cycle_type": "beginner",
            "duration_minutes": 25,
            "recall_score": 85,
            "mcq_score": 90,
            "verbal_transcript": "I learned about Article 14 which ensures equality before the law and Article 17 which abolishes untouchability."
        }
        r = client.post(f"{BASE_URL}/retention/cycle", json=cycle_payload, headers=headers)
        if r.status_code != 200:
            print(f"Cycle submission failed: {r.text}")
            return
        
        print(f"Cycle Result: {r.json()}")
        
        # 3. Verify Knowledge Tree
        print("Fetching Knowledge Tree...")
        r = client.get(f"{BASE_URL}/retention/tree", headers=headers)
        if r.status_code != 200:
            print(f"Tree fetch failed: {r.text}")
            return
        
        tree = r.json()
        # Find the leaf we just updated
        found = False
        for branch in tree:
            for leaf in branch["leaves"]:
                if leaf["topicId"] == "102":
                    print(f"Verified Leaf: {leaf['topicName']} | Score: {leaf['retentionScore']} | Status: {leaf['status']}")
                    found = True
                    break
        
        if not found:
            print("Error: Updated topic not found in tree!")
        else:
            print("Full retention loop verified successfully! ✅")

if __name__ == "__main__":
    verify_flow()
