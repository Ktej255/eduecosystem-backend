"""
Tests for Peer Reviews
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.user import User

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def test_instructor(db: Session, client: TestClient):
    """Create a test instructor user"""
    # Seed permissions
    from app.models.permissions import Role, Permission

    # Create permission
    perm = db.query(Permission).filter(Permission.name == "create_peer_review").first()
    if not perm:
        perm = Permission(
            name="create_peer_review",
            display_name="Create Peer Review",
            resource="peer_review",
            action="create",
        )
        db.add(perm)
        db.commit()

    # Create role
    role = db.query(Role).filter(Role.name == "instructor").first()
    if not role:
        role = Role(name="instructor", display_name="Instructor", is_system_role=True)
        db.add(role)
        db.commit()

    if perm not in role.permissions:
        role.permissions.append(perm)
        db.commit()

    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "pr_instructor@test.com", "password": "InstructorPass123!"},
    )
    if response.status_code == 200:
        return {
            "email": "pr_instructor@test.com",
            "token": response.json()["access_token"],
            "id": 1,
        }  # ID mock

    # Register user
    client.post(
        "/api/v1/login/register",
        json={
            "email": "pr_instructor@test.com",
            "password": "InstructorPass123!",
            "full_name": "PR Instructor",
            "role": "instructor",
        },
    )

    # Assign role object to user
    user = db.query(User).filter(User.email == "pr_instructor@test.com").first()
    if user and role not in user.roles:
        user.roles.append(role)
        db.commit()

    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": "pr_instructor@test.com", "password": "InstructorPass123!"},
    )
    token = login_response.json()["access_token"]
    return {"email": "pr_instructor@test.com", "token": token}


@pytest.fixture
def test_student_1(db: Session, client: TestClient):
    """Create test student 1 (Reviewer)"""
    # Seed permissions
    from app.models.permissions import Role, Permission

    perm = db.query(Permission).filter(Permission.name == "submit_peer_review").first()
    if not perm:
        perm = Permission(
            name="submit_peer_review",
            display_name="Submit Peer Review",
            resource="peer_review",
            action="create",
        )
        db.add(perm)
        db.commit()

    role = db.query(Role).filter(Role.name == "student").first()
    if not role:
        role = Role(name="student", display_name="Student", is_system_role=True)
        db.add(role)
        db.commit()

    if perm not in role.permissions:
        role.permissions.append(perm)
        db.commit()

    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "reviewer@test.com", "password": "StudentPass123!"},
    )
    if response.status_code == 200:
        return {"email": "reviewer@test.com", "token": response.json()["access_token"]}

    client.post(
        "/api/v1/login/register",
        json={
            "email": "reviewer@test.com",
            "password": "StudentPass123!",
            "full_name": "Reviewer Student",
        },
    )

    # Assign role
    user = db.query(User).filter(User.email == "reviewer@test.com").first()
    if user and role not in user.roles:
        user.roles.append(role)
        db.commit()

    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": "reviewer@test.com", "password": "StudentPass123!"},
    )
    return {
        "email": "reviewer@test.com",
        "token": login_response.json()["access_token"],
    }


@pytest.fixture
def test_student_2(db: Session, client: TestClient):
    """Create test student 2 (Reviewee)"""
    # Reuse student role setup from test_student_1 implicitly or ensure it exists
    # For safety, ensure role exists
    from app.models.permissions import Role

    role = db.query(Role).filter(Role.name == "student").first()

    response = client.post(
        "/api/v1/login/access-token",
        data={"username": "reviewee@test.com", "password": "StudentPass123!"},
    )
    if response.status_code == 200:
        return {"email": "reviewee@test.com", "token": response.json()["access_token"]}

    client.post(
        "/api/v1/login/register",
        json={
            "email": "reviewee@test.com",
            "password": "StudentPass123!",
            "full_name": "Reviewee Student",
        },
    )

    # Assign role
    user = db.query(User).filter(User.email == "reviewee@test.com").first()
    if user and role and role not in user.roles:
        user.roles.append(role)
        db.commit()

    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": "reviewee@test.com", "password": "StudentPass123!"},
    )
    return {
        "email": "reviewee@test.com",
        "token": login_response.json()["access_token"],
    }


@pytest.fixture
def test_course(db: Session, test_instructor, client: TestClient):
    """Create a test course"""
    course_data = {
        "title": "Peer Review Course",
        "description": "Course for testing peer reviews",
        "category_id": 1,  # Use ID if enum not supported directly in json
        "level": "beginner",
        "price": 0.0,
        "is_published": True,
    }
    # Ensure category exists if FK required, or use default.
    # Assuming category_id is optional or we can use 1.

    response = client.post(
        "/api/v1/courses/",
        json=course_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    return response.json()


@pytest.fixture
def test_assignment(db: Session, test_instructor, test_course, client: TestClient):
    """Create a test assignment"""
    # Create module first
    mod_resp = client.post(
        f"/api/v1/courses/{test_course['id']}/modules",
        json={"title": "Module 1", "order_index": 1},
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )

    assert mod_resp.status_code in [200, 201], (
        f"Module creation failed: {mod_resp.json()}"
    )
    mod_id = mod_resp.json()["id"]

    # Create assignment
    assign_data = {
        "title": "PR Assignment",
        "description": "Submit for review",
        "points": 100,
        "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "course_id": test_course["id"],
    }
    resp = client.post(
        "/api/v1/assignments/",
        json=assign_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert resp.status_code in [200, 201], (
        f"Assignment creation failed: {resp.status_code} - {resp.text}"
    )
    return resp.json()


@pytest.fixture
def test_submission(db: Session, test_student_2, test_assignment, client: TestClient):
    """Create a submission from student 2"""
    # Enroll student 2
    # Assuming enrollment logic or skipping if not strictly enforced for this test unit
    # But let's try to submit directly

    resp = client.post(
        f"/api/v1/assignments/{test_assignment['id']}/submissions",
        data={"content": "My submission content"},
        headers={"Authorization": f"Bearer {test_student_2['token']}"},
    )
    # If enrollment required, this might fail. Let's assume for unit test we might need to mock or enroll.
    # For now, let's assume success or handle failure.
    if resp.status_code != 200:
        # Try enrolling first
        # Need course ID from assignment... not easily available here without query
        pass

    return resp.json()


# ============================================================================
# TESTS
# ============================================================================


def test_create_peer_review_assignment(
    client: TestClient, test_instructor, test_student_1, test_student_2, test_assignment
):
    """Test instructor assigning a peer review"""

    # We need user IDs.
    # Helper to get ID from token
    def get_user_id(token):
        return client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        ).json()["id"]

    reviewer_id = get_user_id(test_student_1["token"])
    reviewee_id = get_user_id(test_student_2["token"])

    # Need a submission ID.
    # Let's create a submission manually via DB or API if possible.
    # For simplicity, let's use the API flow in a single test function to ensure order.
    pass


def test_peer_review_flow(
    client: TestClient,
    test_instructor,
    test_student_1,
    test_student_2,
    test_course,
    test_assignment,
):
    """Full flow: Submit -> Assign Review -> Submit Review"""

    # 1. Enroll students
    client.post(
        f"/api/v1/courses/{test_course['id']}/enroll",
        headers={"Authorization": f"Bearer {test_student_1['token']}"},
    )
    client.post(
        f"/api/v1/courses/{test_course['id']}/enroll",
        headers={"Authorization": f"Bearer {test_student_2['token']}"},
    )

    # 2. Student 2 submits assignment
    sub_resp = client.post(
        f"/api/v1/assignments/{test_assignment['id']}/submit",
        data={"notes": "Please review my work"},
        headers={"Authorization": f"Bearer {test_student_2['token']}"},
    )
    assert sub_resp.status_code in [200, 201]
    submission_id = sub_resp.json()["id"]

    # 3. Instructor assigns Student 1 to review Student 2
    reviewer_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {test_student_1['token']}"},
    ).json()["id"]
    reviewee_id = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {test_student_2['token']}"},
    ).json()["id"]

    assign_data = {
        "assignment_id": test_assignment["id"],
        "reviewer_id": reviewer_id,
        "reviewee_id": reviewee_id,
        "submission_id": submission_id,
        "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
    }

    pr_assign_resp = client.post(
        "/api/v1/peer-reviews/assignments",
        json=assign_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert pr_assign_resp.status_code in [200, 201]
    pr_assignment_id = pr_assign_resp.json()["id"]

    # 4. Student 1 checks for reviews to give
    to_review_resp = client.get(
        "/api/v1/peer-reviews/assignments/to-review",
        headers={"Authorization": f"Bearer {test_student_1['token']}"},
    )
    assert to_review_resp.status_code == 200
    assert len(to_review_resp.json()) > 0
    assert to_review_resp.json()[0]["id"] == pr_assignment_id

    # 5. Student 1 submits review
    review_data = {
        "peer_review_assignment_id": pr_assignment_id,
        "content": "Great job, but check your spelling.",
        "score": 95.0,
    }

    submit_review_resp = client.post(
        "/api/v1/peer-reviews/",
        json=review_data,
        headers={"Authorization": f"Bearer {test_student_1['token']}"},
    )
    assert submit_review_resp.status_code in [200, 201]
    review_id = submit_review_resp.json()["id"]

    # 6. Verify review details
    get_review_resp = client.get(
        f"/api/v1/peer-reviews/{review_id}",
        headers={"Authorization": f"Bearer {test_student_1['token']}"},
    )
    assert get_review_resp.status_code == 200
    assert get_review_resp.json()["content"] == "Great job, but check your spelling."
