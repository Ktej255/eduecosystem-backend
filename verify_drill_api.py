import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "ktej255@gmail.com"
ADMIN_PASSWORD = "Tej@1106"

def get_token(email, password):
    response = requests.post(
        f"{BASE_URL}/login/access-token",
        data={"username": email, "password": password}
    )
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return None
    return response.json()["access_token"]

def verify_drill():
    # 1. Login as Admin
    print("Logging in as Admin...")
    token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create a Question
    print("Creating Question...")
    question_data = {
        "gs_paper": "GS1",
        "topic": "History",
        "question_text": "Discuss the impact of British rule on Indian economy.",
        "difficulty": "medium",
        "key_points": ["Deindustrialization", "Drain of wealth"]
    }
    response = requests.post(
        f"{BASE_URL}/admin/drill/questions",
        headers=headers,
        json=question_data
    )
    if response.status_code != 200:
        print(f"Failed to create question: {response.text}")
        return
    
    question = response.json()
    print(f"Question created: {question['id']}")
    
    # 3. Start Session (as same user for simplicity, or create new student)
    print("Starting Session...")
    session_data = {
        "date": "2025-12-04",
        "question_number": 1
    }
    response = requests.post(
        f"{BASE_URL}/drill/start-session",
        headers=headers,
        json=session_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print("Session started successfully!")
        print(f"Question Text: {data['data']['text']}")
        if data['data']['text'] == question_data['question_text']:
            print("VERIFICATION SUCCESSFUL: Question text matches.")
        else:
            print("VERIFICATION FAILED: Question text mismatch.")
            
        # 4. Upload Answer
        print("Uploading Answer...")
        answer_data = {
            "date": "2025-12-04",
            "question_number": 1,
            "answer_type": "before",
            "answer_text": "This is my test answer."
        }
        response = requests.post(
            f"{BASE_URL}/drill/upload-answer",
            headers=headers,
            json=answer_data
        )
        if response.status_code == 200:
            print("Answer uploaded successfully!")
        else:
            print(f"Failed to upload answer: {response.text}")
            
        # 5. Generate Report (Mocking report generation for now as it calls AI)
        # Note: We can't easily mock the AI service call in this script without modifying the backend code or mocking the service.
        # However, we can check if the endpoint accepts the request.
        print("Generating Report...")
        report_data = {
            "date": "2025-12-04",
            "question_number": 1,
            "question_text": question_data["question_text"],
            "model_answer": "Model answer text",
            "before_answer_text": "This is my test answer.",
            "after_answer_text": "",
            "content_summary": "Content summary"
        }
        # This might fail if Grok API key is invalid or network issues, but we want to see if it hits the DB logic
        # We'll wrap in try/except or just print status
        response = requests.post(
            f"{BASE_URL}/drill/generate-report",
            headers=headers,
            json=report_data
        )
        print(f"Generate Report Status: {response.status_code}")
        if response.status_code == 200:
            print("Report generated successfully!")
        else:
            print(f"Report generation failed (expected if AI service is not configured): {response.text}")

    else:
        print(f"Failed to start session: {response.text}")

if __name__ == "__main__":
    verify_drill()
