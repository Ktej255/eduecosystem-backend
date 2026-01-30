import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash

@pytest.fixture
def test_instructor(db: Session, client: TestClient):
    user = User(
        email="inst_debug@test.com",
        username="inst_debug",
        hashed_password=get_password_hash("password"),
        role="instructor",
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": "inst_debug@test.com", "password": "password"},
    )
    if login_response.status_code != 200:
        print(f"DEBUG FIXTURE: Login failed. {login_response.text}")
    token = login_response.json()["access_token"]
    return {"email": "inst_debug@test.com", "token": token, "id": user.id}

@pytest.fixture
def test_category(db: Session, client: TestClient, test_instructor):
    response = client.post(
        "/api/v1/courses/categories/",
        json={"name": "Debug Category", "slug": "debug-cat"},
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    if response.status_code not in [200, 201]:
        print(f"DEBUG FIXTURE: Category creation failed. {response.status_code} {response.text}")
    return response.json()

@pytest.fixture
def test_course(db: Session, test_instructor, test_category, client: TestClient):
    if "id" not in test_category:
        print(f"DEBUG FIXTURE: test_category missing id. {test_category}")
    course_data = {
        "title": "Debug Course",
        "description": "Debug",
        "category_id": test_category["id"],
        "level": "beginner",
        "price": 0.0,
        "is_published": True,
    }
    response = client.post(
        "/api/v1/courses/",
        json=course_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    if response.status_code not in [200, 201]:
        print(f"DEBUG FIXTURE: Course creation failed. {response.status_code} {response.text}")
    return response.json()

def test_add_lesson_to_module_debug(client: TestClient, test_course, test_instructor):
    course_id = test_course["id"]
    module_data = {"title": "Debug Module", "order_index": 1}
    
    module_response = client.post(
        f"/api/v1/courses/{course_id}/modules",
        json=module_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    print(f"DEBUG: Module Status: {module_response.status_code}")
    print(f"DEBUG: Module Body: {module_response.text}")
    module_id = module_response.json()["id"]
    
    lesson_data = {
        "title": "Debug Lesson",
        "type": "video",
        "order_index": 1,
        "duration_minutes": 15,
    }
    
    response = client.post(
        f"/api/v1/modules/{module_id}/lessons",
        json=lesson_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    print(f"DEBUG: Lesson Status: {response.status_code}")
    print(f"DEBUG: Lesson Body: {response.text}")
    assert response.status_code in [200, 201]
