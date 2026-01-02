import requests
import time

API_URL = "http://localhost:8000/api/v1"

# Minimal PDF content
MINIMAL_PDF = b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF"

def test_pdf_upload():
    print("Testing PDF Upload...")
    
    # 1. Create dummy PDF file
    with open("test.pdf", "wb") as f:
        f.write(MINIMAL_PDF)
    
    # 2. Upload to batch1 save_segment
    url = f"{API_URL}/batch1/cycle/1/day/1/part/1/segment/1"
    files = [
        ('pdf_files', ('test.pdf', open('test.pdf', 'rb'), 'application/pdf'))
    ]
    data = {
        'title': 'Test Segment PDF',
        'key_points': 'Testing PDF persistence',
        'content_type': 'pdf',
        'pdf_names': ['test.pdf']
    }
    
    try:
        response = requests.post(url, data=data, files=files)
        print(f"Upload Status: {response.status_code}")
        print(f"Upload Response: {response.text}")
        
        if response.status_code != 200:
            print("Upload Failed!")
            return

        # 3. Check if available in pdf_study
        print("Checking availability in PDF Study service...")
        check_url = f"{API_URL}/pdf-study/check/1_1_1"
        for i in range(5): # Retry a few times as processing is async? No, we awaited it.
            res = requests.get(check_url)
            print(f"Check Status: {res.status_code}")
            print(f"Check Response: {res.text}")
            if res.status_code == 200 and res.json().get('available'):
                print("SUCCESS: PDF is available for student view!")
                break
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_pdf_upload()
