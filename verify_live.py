import requests
import json
import time

# Live AWS Backend URL found in codebase
BASE_URL = "https://a7z4kjysmp.us-east-1.awsapprunner.com/api/v1"
CYCLE = 1
DAY = 1
PART = 1
SEGMENT = 1

def check_live_deployment():
    print(f"Checking Live Backend: {BASE_URL}")
    print("--- 1. Testing READ (Is new logic live?) ---")
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/batch1/cycle/{CYCLE}/day/{DAY}/part/{PART}",
            timeout=10
        )
        duration = time.time() - start_time
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {duration:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            segments = data.get('segments', [])
            
            if segments:
                print(f"✅ Live Backend is UP. Found {len(segments)} segments.")
                segment_1 = next((s for s in segments if s['id'] == 1), None)
                if segment_1:
                    print(f"Segment 1 Title: {segment_1.get('title')}")
                    print(f"Segment 1 Video: {segment_1.get('video_url')}")
                    print(f"Segment 1 Type:  {segment_1.get('content_type')}")
                    
                    # Logic Check
                    # If it returns "Segment 1 (Not Uploaded)" it means DB is empty or logic is working (default)
                    # If it returns the content recently uploaded by user, it PROVES persistence.
                    pass
            else:
                print("❌ Live Backend returned no segments.")
        else:
            print(f"❌ Live Backend Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    check_live_deployment()
