import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.live_class import LiveClass, LiveClassAttendance, LiveClassStatus


@pytest.fixture
def instructor_user(db: Session) -> User:
    """Create an instructor user for testing"""
    from app.core.security import get_password_hash
    from app.models.user import User
    import app.crud.permissions as crud_permissions
    from app.schemas.permissions import RoleCreate, PermissionCreate

    print(f"DEBUG: crud_permissions type: {type(crud_permissions)}")
    print(f"DEBUG: crud_permissions dir: {dir(crud_permissions)}")

    # Create necessary permissions
    perms = [
        "create_live_class",
        "edit_live_class",
        "delete_live_class",
        "manage_live_class",
    ]
    perm_objs = []
    for perm_name in perms:
        perm = crud_permissions.get_permission_by_name(db, name=perm_name)
        if not perm:
            perm_in = PermissionCreate(
                name=perm_name,
                display_name=perm_name.replace("_", " ").title(),
                resource="live_class",
                action=perm_name.split("_")[0],
            )
            perm = crud_permissions.create_permission(db, permission=perm_in)
        perm_objs.append(perm)

    # Create instructor role if doesn't exist
    role = crud_permissions.get_role_by_name(db, name="instructor")
    if not role:
        role_in = RoleCreate(
            name="instructor",
            display_name="Instructor",
            description="Instructor role",
            permission_ids=[p.id for p in perm_objs],
        )
        role = crud_permissions.create_role(db, role=role_in)
    else:
        # Ensure role has permissions (simplified for test)
        pass

    user = User(
        email="instructor@test.com",
        username="instructor",
        hashed_password=get_password_hash("password"),
        full_name="Test Instructor",
        is_active=True,
        role="instructor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Assign role to user
    crud_permissions.assign_role_to_user(db, user_id=user.id, role_id=role.id)

    return user


@pytest.fixture
def student_user(db: Session) -> User:
    """Create a student user for testing"""
    from app.core.security import get_password_hash
    from app.schemas.permissions import PermissionCreate, RoleCreate
    import app.crud.permissions as crud_permissions

    user = User(
        email="student@test.com",
        username="student",
        hashed_password=get_password_hash("password"),
        full_name="Test Student",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create permission
    perm_name = "join_live_class"
    perm = crud_permissions.get_permission_by_name(db, name=perm_name)
    if not perm:
        perm_in = PermissionCreate(
            name=perm_name,
            display_name="Join Live Class",
            description="Join live class",
            resource="live_class",
            action="join",
        )
        perm = crud_permissions.create_permission(db, permission=perm_in)

    # Create role
    role = crud_permissions.get_role_by_name(db, name="student")
    if not role:
        role_in = RoleCreate(
            name="student",
            display_name="Student",
            description="Student role",
            permission_ids=[perm.id],
        )
        role = crud_permissions.create_role(db, role=role_in)

    # Assign role to user
    crud_permissions.assign_role_to_user(db, user_id=user.id, role_id=role.id)

    return user


@pytest.fixture
def test_course(db: Session, instructor_user: User) -> Course:
    """Create a test course"""
    course = Course(
        title="Test Course for Live Classes",
        slug="test-course-live-classes",
        description="Course to test live classes",
        instructor_id=instructor_user.id,
        is_published=True,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@pytest.fixture
def enrolled_student(
    db: Session, test_course: Course, student_user: User
) -> Enrollment:
    """Enroll student in test course"""
    enrollment = Enrollment(user_id=student_user.id, course_id=test_course.id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def test_create_live_class(
    client: TestClient, db: Session, test_course: Course, instructor_user: User
):
    """Test creating a new live class"""
    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create live class
    scheduled_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    response = client.post(
        f"/api/v1/live-classes/courses/{test_course.id}/live-classes",
        json={
            "course_id": test_course.id,
            "title": "Introduction to React",
            "description": "Learn React basics",
            "scheduled_at": scheduled_time,
            "duration_minutes": 60,
            "meeting_url": "https://zoom.us/j/123456789",
            "platform": "zoom",
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Introduction to React"
    assert data["course_id"] == test_course.id
    assert data["status"] == "scheduled"
    assert data["instructor_id"] == instructor_user.id


def test_get_course_live_classes(
    client: TestClient, db: Session, test_course: Course, instructor_user: User
):
    """Test retrieving all live classes for a course"""
    # Create multiple live classes
    for i in range(3):
        scheduled_time = datetime.utcnow() + timedelta(days=i + 1)
        live_class = LiveClass(
            course_id=test_course.id,
            title=f"Class {i + 1}",
            scheduled_at=scheduled_time,
            duration_minutes=60,
            instructor_id=instructor_user.id,
            platform="zoom",
        )
        db.add(live_class)
    db.commit()

    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get all live classes
    response = client.get(
        f"/api/v1/live-classes/courses/{test_course.id}/live-classes", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_start_live_class(
    client: TestClient, db: Session, test_course: Course, instructor_user: User
):
    """Test starting a live class"""
    # Create a scheduled class
    scheduled_time = datetime.utcnow() + timedelta(hours=1)
    live_class = LiveClass(
        course_id=test_course.id,
        title="Test Class",
        scheduled_at=scheduled_time,
        duration_minutes=60,
        instructor_id=instructor_user.id,
        status=LiveClassStatus.SCHEDULED,
    )
    db.add(live_class)
    db.commit()
    db.refresh(live_class)

    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start the class
    response = client.post(
        f"/api/v1/live-classes/{live_class.id}/start", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"


def test_join_live_class(
    client: TestClient,
    db: Session,
    test_course: Course,
    instructor_user: User,
    student_user: User,
    enrolled_student: Enrollment,
):
    """Test student joining a live class"""
    # Create a live class
    scheduled_time = datetime.utcnow()
    live_class = LiveClass(
        course_id=test_course.id,
        title="Test Class",
        scheduled_at=scheduled_time,
        duration_minutes=60,
        instructor_id=instructor_user.id,
        status=LiveClassStatus.LIVE,
        meeting_url="https://zoom.us/j/123",
    )
    db.add(live_class)
    db.commit()
    db.refresh(live_class)

    # Login as student
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Join the class
    response = client.post(
        f"/api/v1/live-classes/{live_class.id}/join", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["live_class_id"] == live_class.id
    assert data["student_id"] == student_user.id
    assert "joined_at" in data


def test_complete_live_class_with_recording(
    client: TestClient, db: Session, test_course: Course, instructor_user: User
):
    """Test completing a live class and adding recording"""
    # Create a live class
    live_class = LiveClass(
        course_id=test_course.id,
        title="Test Class",
        scheduled_at=datetime.utcnow() - timedelta(hours=1),
        duration_minutes=60,
        instructor_id=instructor_user.id,
        status=LiveClassStatus.LIVE,
    )
    db.add(live_class)
    db.commit()
    db.refresh(live_class)

    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Complete the class with recording
    response = client.post(
        f"/api/v1/live-classes/{live_class.id}/complete",
        params={"recording_url": "https://example.com/recording.mp4"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["recording_url"] == "https://example.com/recording.mp4"
    assert data["recording_available"] is True


def test_get_live_class_attendance(
    client: TestClient,
    db: Session,
    test_course: Course,
    instructor_user: User,
    student_user: User,
):
    """Test getting attendance records for a live class"""
    # Create live class
    live_class = LiveClass(
        course_id=test_course.id,
        title="Test Class",
        scheduled_at=datetime.utcnow(),
        duration_minutes=60,
        instructor_id=instructor_user.id,
    )
    db.add(live_class)
    db.commit()

    # Add attendance record
    attendance = LiveClassAttendance(
        live_class_id=live_class.id,
        student_id=student_user.id,
        joined_at=datetime.utcnow(),
        duration_minutes=55,
    )
    db.add(attendance)
    db.commit()

    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get attendance
    response = client.get(
        f"/api/v1/live-classes/{live_class.id}/attendance", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["student_id"] == student_user.id
    assert data[0]["duration_minutes"] == 55


def test_filter_upcoming_live_classes(
    client: TestClient, db: Session, test_course: Course, instructor_user: User
):
    """Test filtering upcoming live classes"""
    # Create classes at different times
    past_class = LiveClass(
        course_id=test_course.id,
        title="Past Class",
        scheduled_at=datetime.utcnow() - timedelta(hours=2),
        duration_minutes=60,
        instructor_id=instructor_user.id,
        status=LiveClassStatus.COMPLETED,
    )

    upcoming_class = LiveClass(
        course_id=test_course.id,
        title="Upcoming Class",
        scheduled_at=datetime.utcnow() + timedelta(hours=2),
        duration_minutes=60,
        instructor_id=instructor_user.id,
        status=LiveClassStatus.SCHEDULED,
    )

    db.add_all([past_class, upcoming_class])
    db.commit()

    # Login as instructor
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": instructor_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get only upcoming classes
    response = client.get(
        f"/api/v1/live-classes/courses/{test_course.id}/live-classes?upcoming_only=true",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Upcoming Class"
