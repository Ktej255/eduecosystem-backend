import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
CYCLE = 1
DAY = 1
PART = 1
SEGMENT = 1
KEY = f"{CYCLE}_{DAY}_{PART}_{SEGMENT}"

def test_persistence():
    print("--- 1. Testing SAVE (Write to DB) ---")
    payload = {
        "title": f"Persistence Test {int(time.time())}",
        "key_points": "Testing DB Read/Write",
        "content_type": "video",
        "youtube_url": "https://youtu.be/test"
    }
    
    # Save Segment
    try:
        response = requests.post(
            f"{BASE_URL}/batch1/cycle/{CYCLE}/day/{DAY}/part/{PART}/segment/{SEGMENT}",
            data=payload
        )
        print(f"Save Status: {response.status_code}")
        print(f"Save Response: {response.text}")
        
        if response.status_code != 200:
            print("❌ Save Failed!")
            return
        else:
            print("✅ Save Successful")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    print("\n--- 2. Testing READ (Read from DB) ---")
    try:
        # Get Part Content
        response = requests.get(
            f"{BASE_URL}/batch1/cycle/{CYCLE}/day/{DAY}/part/{PART}"
        )
        data = response.json()
        
        # Find our segment
        target_segment = next((s for s in data['segments'] if s['id'] == SEGMENT), None)
        
        if target_segment:
            print(f"Retrieved Title: {target_segment['title']}")
            print(f"Retrieved YouTube: {target_segment['youtube_url']}")
            
            if target_segment['title'] == payload['title']:
                print("✅ PERSISTENCE VERIFIED: Data read back correctly match the saved data.")
            else:
                print(f"❌ MISMATCH: Expected '{payload['title']}', got '{target_segment['title']}'")
                print("This indicates 'get_part_content' might still be reading from OLD JSON instead of DB.")
        else:
            print("❌ Segment not found in response!")
            
    except Exception as e:
        print(f"❌ Read Error: {e}")

if __name__ == "__main__":
    test_persistence()
