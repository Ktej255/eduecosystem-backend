import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.course import Course
from app.models.announcement import CourseAnnouncement, AnnouncementRead


@pytest.fixture
def instructor_user(db: Session) -> User:
    """Create an instructor user with permissions"""
    from app.core.security import get_password_hash
    from app.crud import permissions as crud_permissions
    from app.schemas.permissions import RoleCreate, PermissionCreate

    # 1. Create permissions
    permissions = ["create_announcement", "edit_announcement", "delete_announcement"]
    perm_objs = []
    for perm_name in permissions:
        perm = crud_permissions.get_permission_by_name(db, name=perm_name)
        if not perm:
            perm_in = PermissionCreate(
                name=perm_name,
                display_name=perm_name.replace("_", " ").title(),
                resource="announcement",
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

    # 3. Create User
    user = User(
        email="instructor_announce@test.com",
        username="instructor_announce",
        hashed_password=get_password_hash("password"),
        full_name="Test Instructor",
        is_active=True,
        role="instructor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 4. Assign Role
    crud_permissions.assign_role_to_user(db, user_id=user.id, role_id=role.id)

    return user


@pytest.fixture
def student_user(db: Session) -> User:
    """Create a student user"""
    from app.core.security import get_password_hash

    user = User(
        email="student_announce@test.com",
        username="student_announce",
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
        title="Test Course for Announcements",
        description="Course to test announcements",
        instructor_id=instructor_user.id,
        is_published=True,
        slug=random_lower_string(),
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def test_create_announcement(
    client: TestClient, db: Session, test_course: Course, instructor_user: User
):
    """Test creating a course announcement"""
    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create announcement
    response = client.post(
        f"/api/v1/announcements/courses/{test_course.id}/announcements",
        json={
            "title": "Important Update",
            "content": "Please check the new assignment deadline",
            "is_pinned": False,
            "notify_students": True,
            "course_id": test_course.id,
        },
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Important Update"
    assert data["course_id"] == test_course.id
    assert data["instructor_id"] == instructor_user.id


def test_get_course_announcements(
    client: TestClient, db: Session, test_course: Course, instructor_user: User
):
    """Test retrieving all announcements for a course"""
    # Create multiple announcements
    for i in range(3):
        announcement = CourseAnnouncement(
            course_id=test_course.id,
            title=f"Announcement {i + 1}",
            content=f"Content {i + 1}",
            instructor_id=instructor_user.id,
            is_pinned=(i == 0),
        )
        db.add(announcement)
    db.commit()

    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get announcements
    response = client.get(
        f"/api/v1/announcements/courses/{test_course.id}/announcements", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Pinned announcement should be first
    assert data[0]["is_pinned"] is True


def test_mark_announcement_as_read(
    client: TestClient,
    db: Session,
    test_course: Course,
    instructor_user: User,
    student_user: User,
):
    """Test marking an announcement as read"""
    # Create announcement
    announcement = CourseAnnouncement(
        course_id=test_course.id,
        title="Test Announcement",
        content="Test content",
        instructor_id=instructor_user.id,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    # Login as student
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Mark as read
    response = client.post(
        f"/api/v1/announcements/{announcement.id}/mark-read", headers=headers
    )

    assert response.status_code == 200

    # Verify read record created
    read_record = (
        db.query(AnnouncementRead)
        .filter(
            AnnouncementRead.announcement_id == announcement.id,
            AnnouncementRead.user_id == student_user.id,
        )
        .first()
    )
    assert read_record is not None


def test_get_unread_announcements_count(
    client: TestClient,
    db: Session,
    test_course: Course,
    instructor_user: User,
    student_user: User,
):
    """Test getting unread announcements count"""
    # Create announcements
    for i in range(5):
        announcement = CourseAnnouncement(
            course_id=test_course.id,
            title=f"Announcement {i + 1}",
            content=f"Content {i + 1}",
            instructor_id=instructor_user.id,
        )
        db.add(announcement)
    db.commit()

    # Mark 2 as read
    announcements = db.query(CourseAnnouncement).limit(2).all()
    for announcement in announcements:
        read_record = AnnouncementRead(
            announcement_id=announcement.id, user_id=student_user.id
        )
        db.add(read_record)
    db.commit()

    # Login as student
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get unread count
    response = client.get(
        f"/api/v1/announcements/courses/{test_course.id}/announcements/unread-count",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["unread_count"] == 3


def test_pin_announcement(
    client: TestClient, db: Session, test_course: Course, instructor_user: User
):
    """Test pinning an announcement"""
    # Create announcement
    announcement = CourseAnnouncement(
        course_id=test_course.id,
        title="Test Announcement",
        content="Test content",
        instructor_id=instructor_user.id,
        is_pinned=False,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update announcement to pin it
    response = client.put(
        f"/api/v1/announcements/{announcement.id}",
        json={"is_pinned": True},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_pinned"] is True


def test_delete_announcement(
    client: TestClient, db: Session, test_course: Course, instructor_user: User
):
    """Test deleting an announcement"""
    # Create announcement
    announcement = CourseAnnouncement(
        course_id=test_course.id,
        title="Test Announcement",
        content="Test content",
        instructor_id=instructor_user.id,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Delete announcement
    response = client.delete(
        f"/api/v1/announcements/{announcement.id}", headers=headers
    )

    assert response.status_code == 204

    # Verify deleted
    deleted = (
        db.query(CourseAnnouncement)
        .filter(CourseAnnouncement.id == announcement.id)
        .first()
    )
    assert deleted is None
