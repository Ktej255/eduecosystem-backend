import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.course import Course
from app.models.discussion import (
    DiscussionCategory,
    DiscussionThread,
    DiscussionPost,
    PostVote,
)


@pytest.fixture
def instructor_user(db: Session) -> User:
    """Create an instructor user"""
    from app.core.security import get_password_hash

    user = User(
        email="instructor_disc@test.com",
        username="instructor_disc",
        hashed_password=get_password_hash("password"),
        full_name="Test Instructor",
        role="instructor",
        is_superuser=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def student_user(db: Session) -> User:
    """Create a student user"""
    from app.core.security import get_password_hash

    user = User(
        email="student_disc@test.com",
        username="student_disc",
        hashed_password=get_password_hash("password"),
        full_name="Test Student",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_course(db: Session, instructor_user: User) -> Course:
    """Create a test course"""
    from app.tests.utils.utils import random_lower_string

    course = Course(
        title="Test Course for Discussions",
        description="Course to test discussions",
        instructor_id=instructor_user.id,
        is_published=True,
        slug=random_lower_string(),
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@pytest.fixture
def discussion_category(db: Session, test_course: Course) -> DiscussionCategory:
    """Create a discussion category"""
    category = DiscussionCategory(
        course_id=test_course.id,
        name="General Discussion",
        description="General course questions",
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def test_create_discussion_category(
    client: TestClient, db: Session, test_course: Course, instructor_user: User
):
    """Test creating a discussion category"""
    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create category
    response = client.post(
        f"/api/v1/discussions/courses/{test_course.id}/categories",
        json={
            "name": "Q&A",
            "description": "Questions and Answers",
            "order_index": 0,
            "course_id": test_course.id,
        },
        headers=headers,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["name"] == "Q&A"
    assert data["course_id"] == test_course.id


def test_create_discussion_thread(
    client: TestClient,
    db: Session,
    test_course: Course,
    discussion_category: DiscussionCategory,
    student_user: User,
):
    """Test creating a discussion thread"""
    # Login as student
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create thread
    response = client.post(
        "/api/v1/discussions/threads",
        json={
            "course_id": test_course.id,
            "category_id": discussion_category.id,
            "title": "How to install Python?",
            "content": "I'm having trouble installing Python on Windows",
        },
        headers=headers,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["title"] == "How to install Python?"
    assert data["user_id"] == student_user.id


def test_reply_to_thread(
    client: TestClient,
    db: Session,
    test_course: Course,
    discussion_category: DiscussionCategory,
    student_user: User,
    instructor_user: User,
):
    """Test posting a reply to a thread"""
    # Create thread
    thread = DiscussionThread(
        course_id=test_course.id,
        category_id=discussion_category.id,
        title="Test Thread",
        content="Original question",
        user_id=student_user.id,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)

    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Reply to thread
    response = client.post(
        "/api/v1/discussions/posts",
        json={
            "thread_id": thread.id,
            "content": "Here's the answer to your question...",
        },
        headers=headers,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["content"] == "Here's the answer to your question..."
    assert data["thread_id"] == thread.id


def test_vote_on_post(
    client: TestClient,
    db: Session,
    test_course: Course,
    discussion_category: DiscussionCategory,
    student_user: User,
    instructor_user: User,
):
    """Test upvoting a helpful post"""
    # Create thread and post
    thread = DiscussionThread(
        course_id=test_course.id,
        category_id=discussion_category.id,
        title="Test Thread",
        content="Question",
        user_id=student_user.id,
    )
    db.add(thread)
    db.flush()

    post = DiscussionPost(
        thread_id=thread.id, content="Helpful answer", user_id=instructor_user.id
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    # Login as student
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upvote the post
    response = client.post(
        f"/api/v1/discussions/posts/{post.id}/vote",
        json={"vote_type": "upvote"},
        headers=headers,
    )

    assert response.status_code == 200

    # Verify vote created
    vote = (
        db.query(PostVote)
        .filter(PostVote.post_id == post.id, PostVote.user_id == student_user.id)
        .first()
    )
    assert vote is not None
    assert vote.vote_type == "upvote"


def test_mark_answer(
    client: TestClient,
    db: Session,
    test_course: Course,
    discussion_category: DiscussionCategory,
    student_user: User,
    instructor_user: User,
):
    """Test marking a post as the answer"""
    # Create thread and post
    thread = DiscussionThread(
        course_id=test_course.id,
        category_id=discussion_category.id,
        title="Test Thread",
        content="Question",
        user_id=student_user.id,
    )
    db.add(thread)
    db.flush()

    post = DiscussionPost(
        thread_id=thread.id, content="The answer", user_id=instructor_user.id
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    # Login as thread author
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Mark as answer
    response = client.post(
        f"/api/v1/discussions/posts/{post.id}/mark-answer", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_answer"] is True


def test_search_threads(
    client: TestClient,
    db: Session,
    test_course: Course,
    discussion_category: DiscussionCategory,
    student_user: User,
):
    """Test searching discussion threads"""
    # Create threads
    thread1 = DiscussionThread(
        course_id=test_course.id,
        category_id=discussion_category.id,
        title="Python installation guide",
        content="How to install Python",
        user_id=student_user.id,
    )
    thread2 = DiscussionThread(
        course_id=test_course.id,
        category_id=discussion_category.id,
        title="JavaScript basics",
        content="Learn JS",
        user_id=student_user.id,
    )
    db.add_all([thread1, thread2])
    db.commit()

    # Login as student
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Search for "Python"
    response = client.get(
        f"/api/v1/discussions/courses/{test_course.id}/threads/search?query=Python",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("Python" in thread["title"] for thread in data)


def test_get_thread_with_posts(
    client: TestClient,
    db: Session,
    test_course: Course,
    discussion_category: DiscussionCategory,
    student_user: User,
):
    """Test getting a thread with all its posts"""
    # Create thread with posts
    thread = DiscussionThread(
        course_id=test_course.id,
        category_id=discussion_category.id,
        title="Test Thread",
        content="Question",
        user_id=student_user.id,
    )
    db.add(thread)
    db.flush()

    for i in range(3):
        post = DiscussionPost(
            thread_id=thread.id, content=f"Reply {i + 1}", user_id=student_user.id
        )
        db.add(post)
    db.commit()
    db.refresh(thread)

    # Login as student
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get thread
    response = client.get(f"/api/v1/discussions/threads/{thread.id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == thread.id
    assert "posts" in data
    assert len(data["posts"]) == 3


def test_filter_unanswered_threads(
    client: TestClient,
    db: Session,
    test_course: Course,
    discussion_category: DiscussionCategory,
    student_user: User,
):
    """Test filtering for unanswered threads"""
    # Create answered thread
    answered_thread = DiscussionThread(
        course_id=test_course.id,
        category_id=discussion_category.id,
        title="Answered Thread",
        content="Question",
        user_id=student_user.id,
        is_resolved=True,
    )

    # Create unanswered thread
    unanswered_thread = DiscussionThread(
        course_id=test_course.id,
        category_id=discussion_category.id,
        title="Unanswered Thread",
        content="Question",
        user_id=student_user.id,
        is_resolved=False,
    )

    db.add_all([answered_thread, unanswered_thread])
    db.commit()

    # Login as student
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get unanswered only
    response = client.get(
        f"/api/v1/discussions/courses/{test_course.id}/threads?is_resolved=false",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert all(not thread["is_resolved"] for thread in data)
