"""
Tests for Question Banks and Quiz Generation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# FIXTURES
# ============================================================================

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def test_instructor(db: Session):
    """Create a test instructor user with necessary permissions"""
    from app.crud import user as crud_user
    from app.crud import permissions as crud_permissions
    from app.schemas.user import UserCreate
    from app.schemas.permissions import RoleCreate, PermissionCreate
    from app.core.security import create_access_token

    # 1. Create permissions
    permissions = ["create_question_bank", "edit_question_bank", "delete_question_bank"]
    perm_objs = []
    for perm_name in permissions:
        perm = crud_permissions.get_permission_by_name(db, name=perm_name)
        if not perm:
            perm_in = PermissionCreate(
                name=perm_name,
                display_name=perm_name.replace("_", " ").title(),
                resource="question_bank",
                action=perm_name.split("_")[0],
            )
            perm = crud_permissions.create_permission(db, permission=perm_in)
        perm_objs.append(perm)

    # 2. Create Role
    role_name = "instructor"
    role = crud_permissions.get_role_by_name(db, name=role_name)
    if not role:
        role_in = RoleCreate(
            name=role_name,
            display_name="Instructor",
            permission_ids=[p.id for p in perm_objs],
        )
        role = crud_permissions.create_role(db, role=role_in)
    else:
        # Ensure permissions are assigned
        # For simplicity in test, we assume if role exists it has permissions or we add them
        # But create_role handles permission assignment. Update might be needed if role exists but lacks perms.
        # Let's just ensure the user has the role.
        pass

    # 3. Create User
    email = "qb_instructor@test.com"
    user = crud_user.get_by_email(db, email=email)
    if not user:
        user_in = UserCreate(
            email=email,
            password="InstructorPass123!",
            full_name="QB Instructor",
            role="instructor",
        )
        user = crud_user.create(db, obj_in=user_in)

    # 4. Assign Role to User
    crud_permissions.assign_role_to_user(db, user_id=user.id, role_id=role.id)

    access_token = create_access_token(subject=user.id)
    return {"email": email, "token": access_token, "id": user.id, "user": user}


@pytest.fixture
def test_course(db: Session, test_instructor):
    """Create a test course"""
    from app.crud import course as crud_course
    from app.schemas.course import CourseCreate

    course_data = CourseCreate(
        title="QB Test Course",
        description="Course for testing question banks",
        category_id=1,  # Assuming category 1 exists or is optional/handled
        level="beginner",
        price=0.0,
        is_published=True,
    )

    # Ensure category exists if needed
    from app.models.category import Category

    category = db.query(Category).first()
    if not category:
        category = Category(name="Test Category", slug="test-category")
        db.add(category)
        db.commit()
        db.refresh(category)

    course_data.category_id = category.id

    # Use crud_course.course instance
    course = crud_course.course.create_with_instructor(
        db, obj_in=course_data, instructor_id=test_instructor["id"]
    )
    return {"id": course.id, "title": course.title}


@pytest.fixture
def test_question_bank(db: Session, test_instructor, test_course):
    """Create a test question bank"""
    from app.crud import question_bank as crud_question_bank
    from app.schemas.question_bank import QuestionBankCreate

    bank_data = QuestionBankCreate(
        title="Test Question Bank",
        description="A bank for testing",
        course_id=test_course["id"],
        category="general",
        difficulty_level="medium",
        is_active=True,
    )

    # Use crud_question_bank.question_bank instance
    bank = crud_question_bank.question_bank.create_with_instructor(
        db, obj_in=bank_data, instructor_id=test_instructor["id"]
    )
    return {"id": bank.id, "course_id": bank.course_id, "title": bank.title}


# ============================================================================
# QUESTION BANK TESTS
# ============================================================================


def test_create_question_bank(client: TestClient, test_instructor, test_course):
    """Test creating a question bank"""
    bank_data = {
        "title": "New Question Bank",
        "description": "Created via test",
        "course_id": test_course["id"],
        "category": "math",
        "difficulty_level": "hard",
        "is_active": True,
    }

    response = client.post(
        "/api/v1/question-banks/question-banks",
        json=bank_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code == 201
    bank = response.json()
    assert bank["title"] == "New Question Bank"
    assert bank["course_id"] == test_course["id"]


def test_list_question_banks(
    client: TestClient, test_instructor, test_course, test_question_bank
):
    """Test listing question banks for a course"""
    response = client.get(
        f"/api/v1/question-banks/courses/{test_course['id']}/question-banks",
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code == 200
    banks = response.json()
    assert len(banks) > 0
    assert banks[0]["id"] == test_question_bank["id"]


def test_update_question_bank(client: TestClient, test_instructor, test_question_bank):
    """Test updating a question bank"""
    update_data = {"title": "Updated Bank Title", "description": "Updated description"}

    response = client.put(
        f"/api/v1/question-banks/question-banks/{test_question_bank['id']}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code == 200
    bank = response.json()
    assert bank["title"] == "Updated Bank Title"


def test_delete_question_bank(client: TestClient, test_instructor, test_question_bank):
    """Test deleting a question bank"""
    response = client.delete(
        f"/api/v1/question-banks/question-banks/{test_question_bank['id']}",
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code == 204

    # Verify deletion
    get_response = client.get(
        f"/api/v1/question-banks/courses/{test_question_bank['course_id']}/question-banks",
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    banks = get_response.json()
    assert not any(b["id"] == test_question_bank["id"] for b in banks)


# ============================================================================
# BANK QUESTION TESTS
# ============================================================================


def test_create_bank_question(client: TestClient, test_instructor, test_question_bank):
    """Test creating a question in a bank"""
    question_data = {
        "text": "What is 2+2?",
        "type": "multiple_choice",
        "points": 1,
        "difficulty": "easy",
        "options": '["1", "2", "3", "4"]',
        "correct_answer": "4",
        "question_bank_ids": [test_question_bank["id"]],
    }

    response = client.post(
        "/api/v1/question-banks/bank-questions",
        json=question_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code == 201
    question = response.json()
    assert question["text"] == "What is 2+2?"

    # Verify it's in the bank
    bank_questions_response = client.get(
        f"/api/v1/question-banks/question-banks/{test_question_bank['id']}/questions",
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    questions = bank_questions_response.json()
    assert len(questions) == 1
    assert questions[0]["id"] == question["id"]


def test_generate_quiz_from_banks(
    client: TestClient, test_instructor, test_course, test_question_bank
):
    """Test generating a quiz from a question bank"""
    # 1. Create a quiz first
    quiz_data = {
        "title": "Generated Quiz",
        "description": "Auto generated",
        "course_id": test_course["id"],
        "time_limit_minutes": 30,
        "passing_score": 70,
    }
    quiz_response = client.post(
        f"/api/v1/quizzes/?course_id={test_course['id']}",
        json=quiz_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    quiz_id = quiz_response.json()["id"]

    # 2. Add questions to the bank
    for i in range(5):
        client.post(
            "/api/v1/question-banks/bank-questions",
            json={
                "text": f"Question {i}",
                "type": "multiple_choice",
                "points": 1,
                "difficulty": "medium",
                "options": '["A", "B"]',
                "correct_answer": "A",
                "question_bank_ids": [test_question_bank["id"]],
            },
            headers={"Authorization": f"Bearer {test_instructor['token']}"},
        )

    # 3. Generate quiz
    generate_data = {
        "quiz_id": quiz_id,
        "pools": [
            {
                "question_bank_id": test_question_bank["id"],
                "num_questions": 3,
                "difficulty_filter": "medium",
            }
        ],
    }

    response = client.post(
        "/api/v1/question-banks/quizzes/generate-from-banks",
        json=generate_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["total_questions_added"] == 3

    # 4. Verify questions added to quiz
    quiz_details = client.get(
        f"/api/v1/quizzes/{quiz_id}",
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    questions = quiz_details.json()["questions"]
    assert len(questions) == 3
