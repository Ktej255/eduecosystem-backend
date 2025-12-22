from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.daily_action import DailyTask, Habit, DailyReflection

def test_create_daily_task(client: TestClient, superuser_token_headers: dict, db: Session) -> None:
    data = {"title": "Test Task", "date": "2023-10-27", "completed": False}
    response = client.post(
        f"{settings.API_V1_STR}/daily-actions/tasks", headers=superuser_token_headers, json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["completed"] == data["completed"]
    assert "id" in content

def test_get_daily_summary(client: TestClient, superuser_token_headers: dict, db: Session) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/daily-actions/today", headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert "tasks" in content
    assert "habits" in content
    assert "reflection" in content
    assert "tasks_completed" in content

def test_create_habit(client: TestClient, superuser_token_headers: dict, db: Session) -> None:
    data = {"name": "Test Habit", "is_active": True}
    response = client.post(
        f"{settings.API_V1_STR}/daily-actions/habits", headers=superuser_token_headers, json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert "id" in content

def test_save_reflection(client: TestClient, superuser_token_headers: dict, db: Session) -> None:
    data = {"content": "Today was a good day.", "date": "2023-10-27"}
    response = client.post(
        f"{settings.API_V1_STR}/daily-actions/reflection", headers=superuser_token_headers, json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["content"] == data["content"]
    assert "id" in content
