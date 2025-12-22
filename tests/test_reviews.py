from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.tests.utils.user import create_random_user, authentication_token_from_email
from app.tests.utils.course import create_random_course
from app.crud import enrollment as crud_enrollment


def test_course_reviews_workflow(
    client: TestClient, db: Session, normal_user_token_headers
) -> None:
    # 1. Create a course (as instructor)
    instructor = create_random_user(db)
    course = create_random_course(db, instructor_id=instructor.id)

    # 2. Enroll user in course
    # We need to get the user from the token
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    user_id = r.json()["id"]

    crud_enrollment.create_enrollment(db, user_id=user_id, course_id=course.id)

    # 3. Create a review
    review_data = {"rating": 5, "review_text": "Great course!", "course_id": course.id}
    r = client.post(
        f"{settings.API_V1_STR}/courses/{course.id}/reviews",
        headers=normal_user_token_headers,
        json=review_data,
    )
    assert r.status_code == 201
    created_review = r.json()
    assert created_review["rating"] == 5
    assert created_review["review_text"] == "Great course!"
    assert created_review["author_name"] is not None

    # 4. Get reviews
    r = client.get(f"{settings.API_V1_STR}/courses/{course.id}/reviews")
    assert r.status_code == 200
    reviews = r.json()
    assert len(reviews) >= 1
    assert reviews[0]["id"] == created_review["id"]

    # 5. Get review breakdown
    r = client.get(f"{settings.API_V1_STR}/courses/{course.id}/reviews/breakdown")
    assert r.status_code == 200
    breakdown = r.json()
    assert breakdown["total_reviews"] >= 1
    assert breakdown["ratings"]["5"] >= 1

    # 6. Get my review
    r = client.get(
        f"{settings.API_V1_STR}/courses/{course.id}/reviews/my-review",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 200
    my_review = r.json()
    assert my_review["id"] == created_review["id"]

    # 7. Update review
    update_data = {"rating": 4, "review_text": "Good course, but could be better."}
    r = client.patch(
        f"{settings.API_V1_STR}/reviews/{created_review['id']}",
        headers=normal_user_token_headers,
        json=update_data,
    )
    assert r.status_code == 200
    updated_review = r.json()
    assert updated_review["rating"] == 4
    assert updated_review["review_text"] == "Good course, but could be better."

    # 8. Mark as helpful (by another user)
    other_user = create_random_user(db)
    other_token = authentication_token_from_email(
        client=client, email=other_user.email, db=db
    )

    r = client.post(
        f"{settings.API_V1_STR}/reviews/{created_review['id']}/helpful",
        headers=other_token,
    )
    assert r.status_code == 200
    assert r.json()["helpful_count"] == 1

    # 9. Check helpful status
    r = client.get(
        f"{settings.API_V1_STR}/courses/{course.id}/reviews", headers=other_token
    )
    reviews = r.json()
    target_review = next(r for r in reviews if r["id"] == created_review["id"])
    assert target_review["helpful_count"] == 1
    assert target_review["has_found_helpful"] == True

    # 10. Unmark helpful
    r = client.post(
        f"{settings.API_V1_STR}/reviews/{created_review['id']}/helpful",
        headers=other_token,
    )
    assert r.status_code == 200
    assert r.json()["helpful_count"] == 0
