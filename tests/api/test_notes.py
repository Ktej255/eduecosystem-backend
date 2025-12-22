import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.lesson import Lesson
from app.models.course import Course
from app.models.module import Module
from app.models.student_notes import LessonNote, LessonBookmark, CourseBookmark


@pytest.fixture
def student_user(db: Session) -> User:
    """Create a student user"""
    from app.core.security import get_password_hash

    user = User(
        email="student_notes@test.com",
        username="student_notes",
        hashed_password=get_password_hash("password"),
        full_name="Test Student",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_course_with_lesson(db: Session, student_user: User):
    """Create a course with module and lesson"""
    course = Course(
        title="Test Course",
        slug="test-course-notes",
        instructor_id=student_user.id,
        is_published=True,
    )
    db.add(course)
    db.flush()

    module = Module(course_id=course.id, title="Test Module", order_index=0)
    db.add(module)
    db.flush()

    lesson = Lesson(
        module_id=module.id,
        title="Test Lesson",
        content="Lesson content",
        order_index=0,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    db.refresh(course)

    return {"course": course, "lesson": lesson}


def test_create_lesson_note(
    client: TestClient, db: Session, student_user: User, test_course_with_lesson
):
    """Test creating a note for a lesson"""
    lesson = test_course_with_lesson["lesson"]

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create note
    response = client.post(
        "/api/v1/notes/notes",
        json={
            "lesson_id": lesson.id,
            "content": "Important concept to remember",
            "timestamp": 120,
            "color": "yellow",
        },
        headers=headers,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["content"] == "Important concept to remember"
    assert data["lesson_id"] == lesson.id
    assert data["user_id"] == student_user.id
    assert data["color"] == "yellow"


def test_get_lesson_notes(
    client: TestClient, db: Session, student_user: User, test_course_with_lesson
):
    """Test retrieving all notes for a lesson"""
    lesson = test_course_with_lesson["lesson"]

    # Create multiple notes
    for i in range(3):
        note = LessonNote(
            lesson_id=lesson.id,
            user_id=student_user.id,
            content=f"Note {i + 1}",
            timestamp=i * 60,
        )
        db.add(note)
    db.commit()

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get notes
    response = client.get(f"/api/v1/notes/lessons/{lesson.id}/notes", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_search_notes(
    client: TestClient, db: Session, student_user: User, test_course_with_lesson
):
    """Test searching notes by content"""
    lesson = test_course_with_lesson["lesson"]

    # Create notes with different content
    note1 = LessonNote(
        lesson_id=lesson.id, user_id=student_user.id, content="Python programming"
    )
    note2 = LessonNote(
        lesson_id=lesson.id, user_id=student_user.id, content="JavaScript basics"
    )
    db.add_all([note1, note2])
    db.commit()

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Search for "Python"
    response = client.get("/api/v1/notes/search?query=Python", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("Python" in note["content"] for note in data)


def test_bookmark_lesson(
    client: TestClient, db: Session, student_user: User, test_course_with_lesson
):
    """Test bookmarking a lesson"""
    lesson = test_course_with_lesson["lesson"]

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Bookmark lesson
    response = client.post(
        "/api/v1/notes/bookmarks/lessons",
        json={
            "lesson_id": lesson.id,
            "course_id": test_course_with_lesson["course"].id,
        },
        headers=headers,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["lesson_id"] == lesson.id
    assert data["user_id"] == student_user.id


def test_unbookmark_lesson(
    client: TestClient, db: Session, student_user: User, test_course_with_lesson
):
    """Test removing a lesson bookmark"""
    lesson = test_course_with_lesson["lesson"]

    # Create bookmark
    bookmark = LessonBookmark(
        lesson_id=lesson.id,
        user_id=student_user.id,
        course_id=test_course_with_lesson["course"].id,
    )
    db.add(bookmark)
    db.commit()

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Unbookmark
    response = client.delete(
        f"/api/v1/notes/bookmarks/lessons/{lesson.id}", headers=headers
    )

    assert response.status_code == 204

    # Verify removed
    removed = (
        db.query(LessonBookmark)
        .filter(
            LessonBookmark.lesson_id == lesson.id,
            LessonBookmark.user_id == student_user.id,
        )
        .first()
    )
    assert removed is None


def test_bookmark_course(
    client: TestClient, db: Session, student_user: User, test_course_with_lesson
):
    """Test bookmarking a course"""
    course = test_course_with_lesson["course"]

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Bookmark course
    response = client.post(
        "/api/v1/notes/bookmarks/courses",
        json={"course_id": course.id},
        headers=headers,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["course_id"] == course.id


def test_get_my_bookmarks(
    client: TestClient, db: Session, student_user: User, test_course_with_lesson
):
    """Test retrieving all bookmarks for current user"""
    lesson = test_course_with_lesson["lesson"]
    course = test_course_with_lesson["course"]

    # Create bookmarks
    lesson_bookmark = LessonBookmark(
        lesson_id=lesson.id, user_id=student_user.id, course_id=course.id
    )
    course_bookmark = CourseBookmark(course_id=course.id, user_id=student_user.id)
    db.add_all([lesson_bookmark, course_bookmark])
    db.commit()

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get bookmarks
    response = client.get("/api/v1/notes/my-notes-and-bookmarks", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "lesson_bookmarks" in data
    assert "course_bookmarks" in data
