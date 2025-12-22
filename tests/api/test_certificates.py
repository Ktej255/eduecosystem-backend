from fastapi.testclient import TestClient
from app.core.config import settings
from app import models


def create_user_and_course(db):
    from app.core.security import get_password_hash

    # Create a user
    user_in = models.User(
        email="cert_user@example.com",
        full_name="Cert User",
        hashed_password=get_password_hash("password"),
    )
    db.add(user_in)
    db.commit()
    db.refresh(user_in)
    # Create a course
    course_in = models.Course(
        title="Test Course",
        slug="test-course",
        description="Test",
        instructor_id=user_in.id
    )
    db.add(course_in)
    db.commit()
    db.refresh(course_in)
    return user_in, course_in


def enroll_user(db, user_id, course_id):
    enrollment = models.Enrollment(
        user_id=user_id,
        course_id=course_id,
        status="completed",
        progress_percentage=100.0,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def test_get_my_certificates(client: TestClient, db):
    user, course = create_user_and_course(db)
    enrollment = enroll_user(db, user.id, course.id)
    # Generate a certificate via internal function
    from app.api.api_v1.endpoints.certificates import generate_certificate_internal

    cert = generate_certificate_internal(db, user.id, course.id, enrollment.id)
    # Authenticate as the user
    login_resp = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": user.email, "password": "password"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Call my certificates endpoint
    resp = client.get(
        f"{settings.API_V1_STR}/certificates/my-certificates", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert any(c["certificate_number"] == cert.certificate_number for c in data)


def test_download_certificate(client: TestClient, db):
    user, course = create_user_and_course(db)
    enrollment = enroll_user(db, user.id, course.id)
    from app.api.api_v1.endpoints.certificates import generate_certificate_internal

    cert = generate_certificate_internal(db, user.id, course.id, enrollment.id)
    login_resp = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": user.email, "password": "password"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        f"{settings.API_V1_STR}/certificates/{cert.certificate_number}/download",
        headers=headers,
    )
    assert resp.status_code == 200
    json_data = resp.json()
    assert "download_url" in json_data
    assert "html_preview" in json_data
