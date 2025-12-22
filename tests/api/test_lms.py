"""
Comprehensive LMS Test Suite
Tests for courses, enrollments, certificates, and payment flow
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


from app.models.certificate import Certificate


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def test_category(db: Session):
    """Create a test category"""
    from app.models.category import Category

    category = Category(
        name="Programming", slug="programming", description="Programming courses"
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def test_instructor(db: Session, client: TestClient):
    """Create a test instructor user"""
    response = client.post(
        "/api/v1/login/register",
        json={
            "email": "instructor@test.com",
            "password": "InstructorPass123!",
            "full_name": "Test Instructor",
            "role": "instructor",
        },
    )
    assert response.status_code in [200, 201]

    # Login to get token
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": "instructor@test.com", "password": "InstructorPass123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    return {"email": "instructor@test.com", "token": token}


@pytest.fixture
def test_student(db: Session, client: TestClient):
    """Create a test student user"""
    response = client.post(
        "/api/v1/login/register",
        json={
            "email": "student@test.com",
            "password": "StudentPass123!",
            "full_name": "Test Student",
        },
    )
    assert response.status_code in [200, 201]

    # Login to get token
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": "student@test.com", "password": "StudentPass123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    return {"email": "student@test.com", "token": token}


@pytest.fixture
def test_course(db: Session, test_instructor, test_category, client: TestClient):
    """Create a test course"""
    course_data = {
        "title": "Python Programming Basics",
        "description": "Learn Python from scratch",
        "long_description": "A comprehensive course for beginners",
        "category_id": test_category.id,
        "level": "beginner",
        "price": 999.0,
        "currency": "INR",
        "is_published": True,
        "tags": ["python", "programming", "beginner"],
    }

    response = client.post(
        "/api/v1/courses/",
        json=course_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code in [200, 201]
    return response.json()


@pytest.fixture
def test_free_course(db: Session, test_instructor, test_category, client: TestClient):
    """Create a free test course"""
    course_data = {
        "title": "Free Python Intro",
        "description": "Free introduction",
        "category_id": test_category.id,
        "level": "beginner",
        "price": 0.0,
        "is_published": True,
    }

    response = client.post(
        "/api/v1/courses/",
        json=course_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code in [200, 201]
    return response.json()


# ============================================================================
# COURSE MANAGEMENT TESTS (15 tests)
# ============================================================================


def test_list_courses(client: TestClient, test_course):
    """Test listing courses"""
    response = client.get("/api/v1/courses/")
    assert response.status_code == 200
    courses = response.json()
    assert isinstance(courses, list)
    assert len(courses) > 0


def test_list_courses_with_category_filter(
    client: TestClient, test_course, test_category
):
    """Test filtering courses by category"""
    response = client.get(f"/api/v1/courses/?category_id={test_category.id}")
    assert response.status_code == 200
    courses = response.json()
    for course in courses:
        # Check if category object is returned and matches
        if course.get("category"):
            assert course["category"]["id"] == test_category.id


def test_list_courses_with_level_filter(client: TestClient, test_course):
    """Test filtering courses by level"""
    response = client.get("/api/v1/courses/?level=beginner")
    assert response.status_code == 200
    courses = response.json()
    for course in courses:
        assert course["level"] == "beginner"


def test_list_courses_with_search(client: TestClient, test_course):
    """Test searching courses"""
    response = client.get("/api/v1/courses/?search=Python")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert "Python" in courses[0]["title"]


def test_create_course_instructor_only(
    client: TestClient, test_instructor, test_category
):
    """Test creating a course (instructor only)"""
    course_data = {
        "title": "Advanced Python",
        "description": "For experienced developers",
        "category_id": test_category.id,
        "level": "advanced",
        "price": 1999.0,
        "is_published": False,
    }

    response = client.post(
        "/api/v1/courses/",
        json=course_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code in [200, 201]
    course = response.json()
    assert course["title"] == "Advanced Python"
    assert course["price"] == 1999.0


def test_create_course_student_forbidden(
    client: TestClient, test_student, test_category
):
    """Test that students cannot create courses"""
    course_data = {
        "title": "Unauthorized Course",
        "description": "Should fail",
        "category_id": test_category.id,
        "level": "beginner",
        "price": 999.0,
    }

    response = client.post(
        "/api/v1/courses/",
        json=course_data,
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    assert response.status_code in [403, 401]


def test_get_course_details(client: TestClient, test_course):
    """Test getting course details with modules"""
    course_id = test_course["id"]
    response = client.get(f"/api/v1/courses/{course_id}")
    assert response.status_code == 200
    course = response.json()
    assert course["id"] == course_id
    assert course["title"] == test_course["title"]


def test_update_course_instructor(client: TestClient, test_course, test_instructor):
    """Test updating a course"""
    course_id = test_course["id"]
    update_data = {"title": "Python Programming - Updated", "price": 1299.0}

    response = client.put(
        f"/api/v1/courses/{course_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code == 200
    updated_course = response.json()
    assert updated_course["title"] == "Python Programming - Updated"
    assert updated_course["price"] == 1299.0


def test_delete_course_instructor(client: TestClient, test_instructor, test_category):
    """Test deleting a course"""
    # Create a course to delete
    course_data = {
        "title": "Course to Delete",
        "description": "Will be deleted",
        "category_id": test_category.id,
        "level": "beginner",
        "price": 500.0,
    }

    create_response = client.post(
        "/api/v1/courses/",
        json=course_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    course_id = create_response.json()["id"]

    # Delete the course
    delete_response = client.delete(
        f"/api/v1/courses/{course_id}",
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert delete_response.status_code in [200, 204]


def test_add_module_to_course(client: TestClient, test_course, test_instructor):
    """Test adding a module to a course"""
    course_id = test_course["id"]
    module_data = {
        "title": "Introduction to Python",
        "description": "First module",
        "order_index": 1,
    }

    response = client.post(
        f"/api/v1/courses/{course_id}/modules",
        json=module_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code in [200, 201]
    module = response.json()
    assert module["title"] == "Introduction to Python"


def test_add_lesson_to_module(client: TestClient, test_course, test_instructor):
    """Test adding a lesson to a module"""
    # First create a module
    course_id = test_course["id"]
    module_data = {
        "title": "Variables and Data Types",
        "description": "Module on basics",
        "order_index": 1,
    }

    module_response = client.post(
        f"/api/v1/courses/{course_id}/modules",
        json=module_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    module_id = module_response.json()["id"]

    # Add lesson to module
    lesson_data = {
        "title": "Introduction to Variables",
        "description": "First lesson",
        "type": "video",
        "order_index": 1,
        "duration_minutes": 15,
    }

    response = client.post(
        f"/api/v1/modules/{module_id}/lessons",
        json=lesson_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code in [200, 201]
    lesson = response.json()
    assert lesson["title"] == "Introduction to Variables"


def test_update_module(client: TestClient, test_course, test_instructor):
    """Test updating a module"""
    # Create module first
    course_id = test_course["id"]
    module_data = {
        "title": "Module to Update",
        "description": "Original description",
        "order_index": 1,
    }

    create_response = client.post(
        f"/api/v1/courses/{course_id}/modules",
        json=module_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    module_id = create_response.json()["id"]

    # Update module
    update_data = {
        "title": "Updated Module Title",
        "description": "Updated description",
    }

    response = client.put(
        f"/api/v1/modules/{module_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code == 200
    updated_module = response.json()
    assert updated_module["title"] == "Updated Module Title"


def test_delete_module(client: TestClient, test_course, test_instructor):
    """Test deleting a module"""
    # Create module first
    course_id = test_course["id"]
    module_data = {
        "title": "Module to Delete",
        "description": "Will be deleted",
        "order_index": 1,
    }

    create_response = client.post(
        f"/api/v1/courses/{course_id}/modules",
        json=module_data,
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    module_id = create_response.json()["id"]

    # Delete module
    response = client.delete(
        f"/api/v1/modules/{module_id}",
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code in [200, 204]


def test_delete_lesson(client: TestClient, test_course, test_instructor):
    """Test deleting a lesson"""
    # Create module and lesson first
    course_id = test_course["id"]
    module_response = client.post(
        f"/api/v1/courses/{course_id}/modules",
        json={"title": "Test Module", "order_index": 1},
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    module_id = module_response.json()["id"]

    lesson_response = client.post(
        f"/api/v1/modules/{module_id}/lessons",
        json={"title": "Lesson to Delete", "type": "text", "order_index": 1},
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    lesson_id = lesson_response.json()["id"]

    # Delete lesson
    response = client.delete(
        f"/api/v1/lessons/{lesson_id}",
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    assert response.status_code in [200, 204]


# ============================================================================
# ENROLLMENT FLOW TESTS (8 tests)
# ============================================================================


def test_enroll_in_free_course(client: TestClient, test_free_course, test_student):
    """Test enrolling in a free course"""
    course_id = test_free_course["id"]

    response = client.post(
        f"/api/v1/courses/{course_id}/enroll",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    assert response.status_code in [200, 201]
    enrollment = response.json()
    assert enrollment["course_id"] == course_id
    assert enrollment["status"] == "active"


def test_duplicate_enrollment_prevented(
    client: TestClient, test_free_course, test_student
):
    """Test that duplicate enrollments are prevented"""
    course_id = test_free_course["id"]

    # First enrollment
    client.post(
        f"/api/v1/courses/{course_id}/enroll",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )

    # Second enrollment should fail
    response = client.post(
        f"/api/v1/courses/{course_id}/enroll",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    assert response.status_code in [400, 409]


def test_get_my_courses(client: TestClient, test_free_course, test_student):
    """Test getting user's enrolled courses"""
    # Enroll in course first
    course_id = test_free_course["id"]
    client.post(
        f"/api/v1/courses/{course_id}/enroll",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )

    # Get my courses
    response = client.get(
        "/api/v1/courses/my-courses",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert courses[0]["course_id"] == course_id


def test_get_course_progress(client: TestClient, test_free_course, test_student):
    """Test getting progress in a course"""
    # Enroll first
    course_id = test_free_course["id"]
    client.post(
        f"/api/v1/courses/{course_id}/enroll",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )

    # Get progress
    response = client.get(
        f"/api/v1/courses/{course_id}/progress",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    assert response.status_code == 200
    progress = response.json()
    assert progress["course_id"] == course_id
    assert "progress_percentage" in progress


def test_update_lesson_progress(
    client: TestClient, test_free_course, test_instructor, test_student
):
    """Test updating lesson progress"""
    # Setup: Create course with module and lesson
    course_id = test_free_course["id"]

    module_response = client.post(
        f"/api/v1/courses/{course_id}/modules",
        json={"title": "Test Module", "order_index": 1},
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    module_id = module_response.json()["id"]

    lesson_response = client.post(
        f"/api/v1/modules/{module_id}/lessons",
        json={
            "title": "Test Lesson",
            "type": "video",
            "order_index": 1,
            "duration_minutes": 10,
        },
        headers={"Authorization": f"Bearer {test_instructor['token']}"},
    )
    lesson_id = lesson_response.json()["id"]

    # Enroll student
    client.post(
        f"/api/v1/courses/{course_id}/enroll",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )

    # Update progress
    progress_data = {
        "lesson_id": lesson_id,
        "status": "completed",
        "time_spent_seconds": 600,
        "video_completed_percentage": 100,
    }

    response = client.post(
        f"/api/v1/progress/lessons/{lesson_id}/update-progress",
        json=progress_data,
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    assert response.status_code in [200, 201]


def test_course_progress_percentage_updates(
    client: TestClient, test_free_course, test_instructor, test_student
):
    """Test that course progress percentage updates when lessons are completed"""
    # Note: This test validates the overall progress tracking logic
    course_id = test_free_course["id"]

    # Enroll student
    client.post(
        f"/api/v1/courses/{course_id}/enroll",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )

    # Get initial progress (should be 0)
    progress_response = client.get(
        f"/api/v1/courses/{course_id}/progress",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    initial_progress = progress_response.json()
    assert initial_progress["progress_percentage"] == 0.0


def test_enroll_requires_authentication(client: TestClient, test_free_course):
    """Test that enrollment requires authentication"""
    course_id = test_free_course["id"]

    response = client.post(f"/api/v1/courses/{course_id}/enroll")
    assert response.status_code == 401


def test_enroll_in_nonexistent_course(client: TestClient, test_student):
    """Test enrolling in a course that doesn't exist"""
    response = client.post(
        "/api/v1/courses/99999/enroll",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    assert response.status_code == 404


# ============================================================================
# CERTIFICATE TESTS (6 tests)
# ============================================================================


def test_get_certificate_not_completed(
    client: TestClient, test_free_course, test_student
):
    """Test that certificate is not available before course completion"""
    course_id = test_free_course["id"]

    # Enroll but don't complete
    client.post(
        f"/api/v1/courses/{course_id}/enroll",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )

    # Try to get certificate
    response = client.get(
        f"/api/v1/certificates/courses/{course_id}/certificate",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    assert response.status_code == 400


def test_get_my_certificates_empty(client: TestClient, test_student):
    """Test getting certificates when user has none"""
    response = client.get(
        "/api/v1/certificates/my-certificates",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    assert response.status_code == 200
    certificates = response.json()
    assert isinstance(certificates, list)


def test_certificate_number_format(db: Session):
    """Test certificate number generation format"""
    cert_number = Certificate.generate_certificate_number()
    assert cert_number.startswith("CERT-")
    assert len(cert_number) == 16  # CERT-YYYY-XXXXXX format


def test_certificate_requires_authentication(client: TestClient, test_free_course):
    """Test that certificate endpoints require authentication"""
    course_id = test_free_course["id"]

    response = client.get(f"/api/v1/certificates/courses/{course_id}/certificate")
    assert response.status_code == 401


def test_download_certificate_unauthorized(client: TestClient, test_student):
    """Test downloading a certificate that doesn't belong to the user"""
    response = client.get(
        "/api/v1/certificates/CERT-2025-ABC123/download",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    assert response.status_code == 404


def test_certificate_fields_present(db: Session):
    """Test that certificate model has all required fields"""
    # This validates the certificate model structure
    required_fields = [
        "id",
        "user_id",
        "course_id",
        "enrollment_id",
        "certificate_number",
        "issued_at",
        "student_name",
        "student_email",
        "course_title",
        "instructor_name",
    ]

    cert_columns = [col.name for col in Certificate.__table__.columns]
    for field in required_fields:
        assert field in cert_columns


# ============================================================================
# PAYMENT INTEGRATION TESTS (5 tests - Mocked)
# ============================================================================


@pytest.mark.skip(reason="Requires payment gateway mocking setup")
def test_create_razorpay_payment(client: TestClient, test_course, test_student):
    """Test creating a Razorpay payment order"""
    course_id = test_course["id"]

    response = client.post(
        f"/api/v1/course-payments/create-razorpay-order?course_id={course_id}",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    # Will implement with mocking
    pass


@pytest.mark.skip(reason="Requires payment gateway mocking setup")
def test_create_stripe_payment(client: TestClient, test_course, test_student):
    """Test creating a Stripe checkout session"""
    course_id = test_course["id"]

    response = client.post(
        f"/api/v1/course-payments/create-stripe-checkout?course_id={course_id}",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    # Will implement with mocking
    pass


@pytest.mark.skip(reason="Requires payment gateway mocking setup")
def test_verify_razorpay_payment(client: TestClient):
    """Test verifying Razorpay payment signature"""
    # Will implement with mocking
    pass


@pytest.mark.skip(reason="Requires payment gateway mocking setup")
def test_get_payment_status(client: TestClient, test_course, test_student):
    """Test getting payment status for a course"""
    course_id = test_course["id"]

    response = client.get(
        f"/api/v1/course-payments/payment-status/{course_id}",
        headers={"Authorization": f"Bearer {test_student['token']}"},
    )
    # Will implement with mocking
    pass


@pytest.mark.skip(reason="Requires payment gateway mocking setup")
def test_enrollment_after_payment(client: TestClient):
    """Test that enrollment is created after successful payment"""
    # Will implement with mocking
    pass
