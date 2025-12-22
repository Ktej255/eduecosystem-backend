import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# from app.main import app # Removed
from app.core.config import settings
from app.tests.utils.user import create_random_user, authentication_token_from_email
from app.tests.utils.course import create_random_course
from app.tests.utils.assignment import create_random_assignment
from app.models.user import User
from app.models.assignment import Assignment
# from app.models.gamification import UserCoin # Removed


# Setup test data
@pytest.fixture
def instructor(db: Session) -> User:
    user = create_random_user(db)
    user.role = "instructor"
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def student1(db: Session) -> User:
    return create_random_user(db, role="student")


@pytest.fixture
def student2(db: Session) -> User:
    return create_random_user(db, role="student")


@pytest.fixture
def assignment(db: Session, instructor: User) -> Assignment:
    course = create_random_course(db, instructor_id=instructor.id)
    return create_random_assignment(db, course_id=course.id)


def test_peer_review_flow(
    client: TestClient,
    db: Session,
    instructor: User,
    student1: User,
    student2: User,
    assignment: Assignment,
) -> None:
    """
    Test complete peer review flow:
    1. Instructor assigns peer review (Student1 reviews Student2)
    2. Student1 sees pending review
    3. Student1 submits review
    4. Student1 gets coin reward
    5. Student2 sees received review
    """

    # 1. Instructor assigns peer review
    instructor_token = authentication_token_from_email(
        client=client, email=instructor.email, db=db
    )
    headers = {"Authorization": f"Bearer {instructor_token}"}

    assign_data = {
        "assignment_id": assignment.id,
        "reviewer_id": student1.id,
        "reviewee_id": student2.id,
        "due_date": "2025-12-31T23:59:59",
    }

    response = client.post(
        f"{settings.API_V1_STR}/peer-reviews/assignments",
        headers=headers,
        json=assign_data,
    )
    assert response.status_code == 201
    pr_assignment = response.json()
    assert pr_assignment["reviewer_id"] == student1.id
    assert pr_assignment["reviewee_id"] == student2.id
    assert pr_assignment["status"] == "pending"

    # 2. Student1 sees pending review
    student1_token = authentication_token_from_email(
        client=client, email=student1.email, db=db
    )
    headers_s1 = {"Authorization": f"Bearer {student1_token}"}

    response = client.get(
        f"{settings.API_V1_STR}/peer-reviews/assignments/to-review",
        headers=headers_s1,
    )
    assert response.status_code == 200
    reviews_to_do = response.json()
    assert len(reviews_to_do) >= 1
    assert any(r["id"] == pr_assignment["id"] for r in reviews_to_do)

    # Check initial coin balance
    db.refresh(student1)
    initial_balance = student1.coins

    # 3. Student1 submits review
    review_data = {
        "peer_review_assignment_id": pr_assignment["id"],
        "rating": 5,
        "feedback": "Great work!",
        "strengths": "Good structure",
        "improvements": "More details needed",
    }

    response = client.post(
        f"{settings.API_V1_STR}/peer-reviews/",
        headers=headers_s1,
        json=review_data,
    )
    assert response.status_code == 201
    review = response.json()
    assert review["rating"] == 5
    assert review["feedback"] == "Great work!"

    # 4. Verify Gamification (Coin Reward)
    # Reload student1 coin balance
    db.expire_all()
    db.refresh(student1)
    updated_balance = student1.coins

    # Should have earned coins (assuming standard reward > 0)
    assert updated_balance > initial_balance

    # Verify transaction record
    from app.models.coin_transaction import CoinTransaction

    transaction = (
        db.query(CoinTransaction)
        .filter(
            CoinTransaction.user_id == student1.id,
            CoinTransaction.reason == "peer_review_submit",
        )
        .first()
    )
    assert transaction is not None

    # 5. Student2 sees received review
    student2_token = authentication_token_from_email(
        client=client, email=student2.email, db=db
    )
    headers_s2 = {"Authorization": f"Bearer {student2_token}"}

    response = client.get(
        f"{settings.API_V1_STR}/peer-reviews/assignments/received",
        headers=headers_s2,
    )
    assert response.status_code == 200
    received_reviews = response.json()
    assert len(received_reviews) >= 1

    # Find the specific review assignment
    received_assignment = next(
        (r for r in received_reviews if r["id"] == pr_assignment["id"]), None
    )
    assert received_assignment is not None
    assert received_assignment["status"] == "submitted"
    assert received_assignment["review"]["rating"] == 5
