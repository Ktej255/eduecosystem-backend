from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.tests.utils.live_class import create_random_live_class


def test_create_poll(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    live_class = create_random_live_class(db)
    data = {
        "question": "What is the capital of France?",
        "options": ["London", "Berlin", "Paris", "Madrid"],
        "correct_option_index": 2,
    }
    response = client.post(
        f"{settings.API_V1_STR}/live-classes-interactive/{live_class.id}/polls",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["question"] == data["question"]
    assert content["options"] == data["options"]
    assert content["live_class_id"] == live_class.id


def test_get_polls(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    live_class = create_random_live_class(db)
    # Create a poll first
    data = {"question": "Test Poll", "options": ["A", "B"], "correct_option_index": 0}
    client.post(
        f"{settings.API_V1_STR}/live-classes-interactive/{live_class.id}/polls",
        headers=superuser_token_headers,
        json=data,
    )

    response = client.get(
        f"{settings.API_V1_STR}/live-classes-interactive/{live_class.id}/polls",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    assert content[0]["question"] == "Test Poll"


def test_ask_question(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    live_class = create_random_live_class(db)
    data = {"question_text": "How does this work?"}
    response = client.post(
        f"{settings.API_V1_STR}/live-classes-interactive/{live_class.id}/questions",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["question_text"] == data["question_text"]
    assert content["is_answered"] is False


def test_send_chat_message(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    live_class = create_random_live_class(db)
    data = {"message": "Hello everyone!"}
    response = client.post(
        f"{settings.API_V1_STR}/live-classes-interactive/{live_class.id}/chat",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == data["message"]
