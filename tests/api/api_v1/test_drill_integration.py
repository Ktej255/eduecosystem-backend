import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.drill import DrillQuestion, DrillContent, DrillModelAnswer
from app.tests.utils.utils import random_email, random_lower_string
from app.tests.utils.user import create_random_user, authentication_token_from_email

def test_drill_integration(
    client: TestClient, db: Session, superuser_token_headers: dict
) -> None:
    # 1. Create a Drill Question (Admin)
    question_data = {
        "gs_paper": "GS1",
        "topic": "History",
        "question_text": "Discuss the impact of British rule on Indian economy.",
        "difficulty": "medium",
        "key_points": ["Deindustrialization", "Drain of wealth"]
    }
    
    # Create question directly in DB or via API
    # Using API to verify Admin API as well
    r = client.post(
        f"{settings.API_V1_STR}/admin/drill/questions",
        headers=superuser_token_headers,
        json=question_data,
    )
    assert r.status_code == 200
    created_question = r.json()
    question_id = created_question["id"]
    
    # Add Content
    content_data = {
        "question_id": question_id,
        "title": "British Economic Impact",
        "sections": [{"heading": "Intro", "text": "The impact was devastating..."}],
        "estimated_reading_time": 10
    }
    r = client.post(
        f"{settings.API_V1_STR}/admin/drill/content",
        headers=superuser_token_headers,
        json=content_data,
    )
    assert r.status_code == 200
    
    # Add Model Answer
    answer_data = {
        "question_id": question_id,
        "title": "Model Answer",
        "answer_text": "The British rule led to...",
        "key_points": ["Point 1", "Point 2"]
    }
    r = client.post(
        f"{settings.API_V1_STR}/admin/drill/model-answers",
        headers=superuser_token_headers,
        json=answer_data,
    )
    assert r.status_code == 200
    
    # 2. Start Session (Student)
    # Create a student user
    email = random_email()
    password = random_lower_string()
    user = create_random_user(db, email=email, password=password)
    user_token_headers = authentication_token_from_email(
        client=client, email=email, db=db
    )
    
    # Start session for Question 1 (which maps to the most recent question)
    r = client.post(
        f"{settings.API_V1_STR}/drill/start-session",
        headers=user_token_headers,
        json={"date": "2025-12-04", "question_number": 1},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["data"]["text"] == question_data["question_text"]
    assert data["data"]["content"]["title"] == content_data["title"]
    assert data["data"]["model_answer"]["title"] == answer_data["title"]
    
    print("Drill integration test passed successfully!")
