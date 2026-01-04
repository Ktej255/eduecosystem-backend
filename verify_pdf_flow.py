
import requests
import os
import sys

# Add parent dir to path to import app modules if needed, but we prefer requests for black box testing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000/api/v1"
TEST_PDF_PATH = "test.pdf"

def check_routes():
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            data = response.json()
            paths = data.get('paths', {}).keys()
            print("\n[INFO] Registered Routes (Batch1):")
            for p in paths:
                if "batch1" in p:
                    print(f"  - {p}")
        else:
            print("[FAIL] Failed to fetch openapi.json")
    except Exception as e:
        print(f"[FAIL] Route check failed: {e}")

def test_pdf_flow():
    print("=== Starting PDF Flow Verification ===")
    
    # 0. Check Status
    print("\n0. Checking API Status...")
    try:
        resp = requests.get(f"{BASE_URL}/status")
        print("Status:", resp.status_code, resp.text)
    except Exception as e:
        print("Status check failed:", e)

    check_routes()
    
    # 1. Simulate Teacher Upload
    print("\n1. Testing Teacher Upload...")
    url = f"{BASE_URL}/batch1/cycle/1/day/1/part/1/segment/1"
    
    # Ensure test PDF exists
    if not os.path.exists(TEST_PDF_PATH):
        print(f"[FAIL] Error: {TEST_PDF_PATH} not found.")
        return

    with open(TEST_PDF_PATH, 'rb') as f:
        files = {
            'pdf_files': ('test.pdf', f, 'application/pdf')
        }
        data = {
            'title': 'Test Segment For PDF',
            'key_points': 'Testing PDF persistence',
            'content_type': 'pdf',
            'pdf_names': 'test.pdf'
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            if response.status_code == 200:
                print("[OK] Upload Success:", response.json())
            else:
                print("[FAIL] Upload Failed:", response.status_code, response.text)
                # Don't return, continue to check if partial upload worked or previously uploaded
        except Exception as e:
            print(f"[FAIL] Connection Failed: {e}")
            return

    # 2. Verify Student Retrieval (List of segments)
    print("\n2. Testing Student Content Retrieval...")
    url_student = f"{BASE_URL}/batch1/cycle/1/day/1/part/1"
    try:
        response = requests.get(url_student)
        if response.status_code == 200:
            data = response.json()
            segments = data.get('segments', [])
            target_segment = next((s for s in segments if s['id'] == 1), None)
            
            if target_segment:
                print("[OK] Segment found in student response")
                print(f"   Title: {target_segment.get('title')}")
                print(f"   Content Type: {target_segment.get('content_type')}")
                pdfs = target_segment.get('pdf_files', [])
                if pdfs and len(pdfs) > 0:
                     print(f"[OK] PDF Files found: {len(pdfs)}")
                else:
                     print("[FAIL] No PDF files found in segment response")
            else:
                print("[FAIL] Segment 1 not found in response")
        else:
             print("[FAIL] Failed to get student content:", response.status_code)
    except Exception as e:
        print(f"[FAIL] Connection Failed: {e}")

    # 3. Verify PDF Availability for Study (Check Endpoint)
    print("\n3. Testing PDF Availability Check...")
    segment_key = "1_1_1_1" # cycle_day_part_seg
    url_check = f"{BASE_URL}/pdf-study/check/{segment_key}"
    
    try:
        response = requests.get(url_check)
        if response.status_code == 200:
            data = response.json()
            if data.get('available'):
                print("[OK] PDF marked as available for study")
                print(f"   Page Count: {data.get('page_count')}")
            else:
                print("[FAIL] PDF NOT marked as available")
                print("   Debug:", data)
        else:
            print("[FAIL] Check failed:", response.status_code, response.text)
    except Exception as e:
        print(f"[FAIL] Connection Failed: {e}")

    # 4. Verify PDF Page Retrieval
    print("\n4. Testing PDF Page Retrieval...")
    url_page = f"{BASE_URL}/pdf-study/page/{segment_key}/1"
    try:
        response = requests.get(url_page)
        if response.status_code == 200:
            data = response.json()
            if data.get('text'):
                print("[OK] Page 1 text retrieved successfully")
                print(f"   Text preview: {data.get('text')[:50]}...")
            else:
                print("[FAIL] Page content missing text")
        else:
            print("[FAIL] Page retrieval failed:", response.status_code, response.text)
    except Exception as e:
        print(f"[FAIL] Connection Failed: {e}")

if __name__ == "__main__":
    test_pdf_flow()
