from fastapi.testclient import TestClient
from app.core.config import settings
from app.crud import user as crud_user
from app.schemas.user import UserCreate


def test_exam_monitoring_flow(client: TestClient, db):
    # Create user and login
    email = "monitor@example.com"
    password = "password"
    user_in = UserCreate(email=email, password=password, full_name="Monitor User")
    user = crud_user.create(db, obj_in=user_in)

    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start Exam
    r = client.post(
        f"{settings.API_V1_STR}/monitoring/exam/start?exam_name=TestExam",
        headers=headers,
    )
    assert r.status_code == 200
    session_id = r.json()["session_id"]

    # Log Violation
    r = client.post(
        f"{settings.API_V1_STR}/monitoring/exam/violation?session_id={session_id}&violation_type=tab_switch",
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["total_violations"] == 1

    # End Exam
    r = client.post(
        f"{settings.API_V1_STR}/monitoring/exam/end?session_id={session_id}",
        headers=headers,
    )
    assert r.status_code == 200
