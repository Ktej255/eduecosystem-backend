import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.course import Course
from app.models.learning_path import LearningPath, PathCourse, PathEnrollment


@pytest.fixture
def creator_user(db: Session) -> User:
    """Create a creator user for learning paths"""
    from app.core.security import get_password_hash
    from app.models.permissions import Role, Permission

    # Create permission
    perm = Permission(
        name="create_learning_path",
        display_name="Create Learning Path",
        resource="learning_path",
        action="create",
    )
    db.add(perm)
    db.commit()

    # Create role (check if exists first to avoid conflict with other tests if running in parallel/same session)
    role = db.query(Role).filter(Role.name == "instructor").first()
    if not role:
        role = Role(name="instructor", display_name="Instructor", is_system_role=True)
        db.add(role)
        db.commit()

    if perm not in role.permissions:
        role.permissions.append(perm)
        db.commit()

    user = User(
        email="creator@test.com",
        username="creator",
        hashed_password=get_password_hash("password"),
        full_name="Path Creator",
        is_active=True,
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def student_user(db: Session) -> User:
    """Create a student user"""
    from app.core.security import get_password_hash

    user = User(
        email="student@test.com",
        username="student_lp",
        hashed_password=get_password_hash("password"),
        full_name="Test Student",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_courses(db: Session, creator_user: User):
    """Create multiple test courses for path"""
    import re

    courses = []
    for i in range(3):
        title = f"Course {i + 1}"
        # Generate slug from title
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        course = Course(
            title=title,
            slug=f"{slug}-{i + 1}",  # Add counter to ensure uniqueness
            description=f"Test course {i + 1}",
            instructor_id=creator_user.id,
            is_published=True,
        )
        db.add(course)
        courses.append(course)

    db.commit()
    for course in courses:
        db.refresh(course)
    return courses


def test_create_learning_path(client: TestClient, db: Session, creator_user: User):
    """Test creating a new learning path"""
    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": creator_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create learning path
    response = client.post(
        "/api/v1/learning-paths/",
        json={
            "title": "Full Stack Developer Path",
            "description": "Complete path to becoming a full stack developer",
            "slug": "full-stack-dev",
            "difficulty_level": "intermediate",
            "estimated_duration_hours": 200,
            "price": 0.0,
            "is_published": True,
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Full Stack Developer Path"
    assert data["difficulty_level"] == "intermediate"
    assert data["slug"] == "full-stack-dev"
    assert data["creator_id"] == creator_user.id


def test_add_courses_to_path(
    client: TestClient, db: Session, creator_user: User, test_courses
):
    """Test adding courses to a learning path"""
    # Create learning path
    path = LearningPath(
        title="Test Path",
        description="Test",
        slug="test-path",
        creator_id=creator_user.id,
        is_published=True,
    )
    db.add(path)
    db.commit()
    db.refresh(path)

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": creator_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add first course
    response = client.post(
        f"/api/v1/learning-paths/{path.id}/courses",
        json={
            "path_id": path.id,
            "course_id": test_courses[0].id,
            "order_index": 0,
            "is_required": True,
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["course_id"] == test_courses[0].id
    assert data["order_index"] == 0


def test_add_course_with_prerequisite(
    client: TestClient, db: Session, creator_user: User, test_courses
):
    """Test adding course with prerequisite"""
    # Create path with courses
    path = LearningPath(
        title="Test Path",
        slug="test-path",
        creator_id=creator_user.id,
        is_published=True,
    )
    db.add(path)
    db.commit()

    # Add first course (no prerequisite)
    path_course1 = PathCourse(
        path_id=path.id, course_id=test_courses[0].id, order_index=0
    )
    db.add(path_course1)
    db.commit()
    db.refresh(path_course1)

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": creator_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add second course with prerequisite
    response = client.post(
        f"/api/v1/learning-paths/{path.id}/courses",
        json={
            "path_id": path.id,
            "course_id": test_courses[1].id,
            "order_index": 1,
            "prerequisite_course_id": test_courses[0].id,
            "is_required": True,
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["prerequisite_course_id"] == test_courses[0].id


def test_enroll_in_path(
    client: TestClient,
    db: Session,
    creator_user: User,
    student_user: User,
    test_courses,
):
    """Test student enrollment in learning path"""
    # Create path with courses
    path = LearningPath(
        title="Test Path",
        slug="test-path",
        creator_id=creator_user.id,
        is_published=True,
        price=0.0,
    )
    db.add(path)
    db.commit()

    # Add courses to path
    for i, course in enumerate(test_courses):
        path_course = PathCourse(path_id=path.id, course_id=course.id, order_index=i)
        db.add(path_course)
    db.commit()

    # Login as student
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Enroll in path
    response = client.post(f"/api/v1/learning-paths/{path.id}/enroll", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["path_id"] == path.id
    assert data["student_id"] == student_user.id
    assert data["total_courses"] == 3
    assert data["completed_courses"] == 0
    assert data["progress_percentage"] == 0.0


def test_get_learning_path_by_slug(
    client: TestClient, db: Session, creator_user: User, test_courses
):
    """Test retrieving learning path by slug"""
    # Create path
    path = LearningPath(
        title="Test Path",
        description="Test description",
        slug="test-path-slug",
        creator_id=creator_user.id,
        difficulty_level="beginner",
        is_published=True,
    )
    db.add(path)
    db.commit()

    # Add a course
    path_course = PathCourse(
        path_id=path.id, course_id=test_courses[0].id, order_index=0
    )
    db.add(path_course)
    db.commit()

    # Get by slug
    response = client.get("/api/v1/learning-paths/slug/test-path-slug")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Path"
    assert data["slug"] == "test-path-slug"
    assert len(data["path_courses"]) == 1


def test_filter_paths_by_difficulty(
    client: TestClient, db: Session, creator_user: User
):
    """Test filtering learning paths by difficulty"""
    # Create paths with different difficulties
    difficulties = ["beginner", "intermediate", "advanced"]
    for difficulty in difficulties:
        path = LearningPath(
            title=f"{difficulty.capitalize()} Path",
            slug=f"{difficulty}-path",
            creator_id=creator_user.id,
            difficulty_level=difficulty,
            is_published=True,
        )
        db.add(path)
    db.commit()

    # Filter for intermediate only
    response = client.get("/api/v1/learning-paths/?difficulty=intermediate")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["difficulty_level"] == "intermediate"


def test_check_course_access_without_prerequisite_completion(
    client: TestClient,
    db: Session,
    creator_user: User,
    student_user: User,
    test_courses,
):
    """Test checking course access when prerequisite not completed"""
    # Create path
    path = LearningPath(
        title="Test Path",
        slug="test-path",
        creator_id=creator_user.id,
        is_published=True,
    )
    db.add(path)
    db.commit()

    # Add courses with prerequisite
    path_course1 = PathCourse(
        path_id=path.id, course_id=test_courses[0].id, order_index=0
    )
    path_course2 = PathCourse(
        path_id=path.id,
        course_id=test_courses[1].id,
        order_index=1,
        prerequisite_course_id=test_courses[0].id,
    )
    db.add_all([path_course1, path_course2])
    db.commit()

    # Enroll student
    enrollment = PathEnrollment(
        path_id=path.id, student_id=student_user.id, total_courses=2
    )
    db.add(enrollment)
    db.commit()

    # Login as student
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Check access to second course (should be denied)
    response = client.get(
        f"/api/v1/learning-paths/{path.id}/course/{test_courses[1].id}/access",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["has_access"] is False


def test_get_my_path_enrollments(
    client: TestClient,
    db: Session,
    creator_user: User,
    student_user: User,
    test_courses,
):
    """Test getting student's path enrollments"""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    # Create paths and enroll
    for i in range(2):
        path = LearningPath(
            title=f"Path {i + 1}",
            slug=f"path-{i + 1}",
            creator_id=creator_user.id,
            is_published=True,
            created_at=now,
            updated_at=now,
        )
        db.add(path)
        db.flush()

        enrollment = PathEnrollment(
            path_id=path.id,
            student_id=student_user.id,
            total_courses=1,
            completed_courses=0,
            enrolled_at=now,
            last_accessed_at=now,
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

    db.commit()

    # Login as student
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": student_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get enrollments
    response = client.get("/api/v1/learning-paths/my-enrollments", headers=headers)

    if response.status_code != 200:
        with open("error_log.txt", "w") as f:
            f.write(f"Response status: {response.status_code}\n")
            f.write(f"Response body: {response.json()}\n")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("path" in enrollment for enrollment in data)


def test_update_path_course_order(
    client: TestClient, db: Session, creator_user: User, test_courses
):
    """Test updating course order in path"""
    # Create path with course
    path = LearningPath(
        title="Test Path",
        slug="test-path",
        creator_id=creator_user.id,
        is_published=True,
    )
    db.add(path)
    db.commit()

    path_course = PathCourse(
        path_id=path.id, course_id=test_courses[0].id, order_index=0
    )
    db.add(path_course)
    db.commit()
    db.refresh(path_course)

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": creator_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update order
    response = client.put(
        f"/api/v1/learning-paths/courses/{path_course.id}",
        json={"order_index": 5},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["order_index"] == 5
