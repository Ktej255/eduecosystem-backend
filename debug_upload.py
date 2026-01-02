import requests
import json

API_URL = "http://localhost:8000/api/v1/batch1/cycle/1/day/1/part/1/segment/4"

def test_upload():
    # Mock PDF content
    pdf_content = b"%PDF-1.4 mock content"
    files = [
        ('pdf_files', ('test.pdf', pdf_content, 'application/pdf'))
    ]
    
    # Mock preserved data (empty list)
    preserved_data = json.dumps([])
    
    data = {
        'title': 'Test Segment 3',
        'key_points': 'Testing PDF upload',
        'content_type': 'pdf',
        'pdf_names': ['test.pdf'],
        'preserved_pdf_data': preserved_data
    }
    
    try:
        print(f"Sending request to {API_URL}...")
        response = requests.post(API_URL, files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("Upload Success!")
        else:
            print("Upload Failed!")
            
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    test_upload()
