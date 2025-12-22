from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.course_review import CourseReview, ReviewHelpful
from app.crud import course as crud_course
from app.crud import enrollment as crud_enrollment
from app.schemas.course import (
    Course as CourseSchema,
    CourseCreate,
    CourseUpdate,
    CourseWithModules,
    CourseListItem,
    Module as ModuleSchema,
    ModuleCreate,
    ModuleUpdate,
    ModuleWithLessons,
    Lesson as LessonSchema,
    LessonCreate,
    LessonUpdate,
    Enrollment as EnrollmentSchema,
    EnrollmentWithCourse,
    CourseReviewCreate,
    CourseReview as CourseReviewSchema,
)

router = APIRouter()
modules_router = APIRouter()
lessons_router = APIRouter()

# ============================================================================
# COURSE ENDPOINTS
# ============================================================================


@router.get("/", response_model=List[CourseListItem])
def list_courses(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    category_id: Optional[int] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    tag_ids: Optional[List[int]] = Query(None),
    sort_by: Optional[str] = "newest",
    is_published: bool = True,
) -> Any:
    """
    List all courses with optional filters
    """
    courses = crud_course.course.get_multi(
        db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        level=level,
        is_published=is_published,
        search=search,
        min_price=min_price,
        max_price=max_price,
        tag_ids=tag_ids,
        sort_by=sort_by,
    )
    return courses


@router.post("/", response_model=CourseSchema, status_code=status.HTTP_201_CREATED)
def create_course(
    *,
    db: Session = Depends(deps.get_db),
    course_in: CourseCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new course (instructor only)
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    course = crud_course.course.create_with_instructor(
        db=db, obj_in=course_in, instructor_id=current_user.id
    )
    return course


@router.get("/my-courses", response_model=List[EnrollmentWithCourse])
def get_my_courses(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all courses the current user is enrolled in
    """
    enrollments = crud_enrollment.get_enrollments_by_user(
        db=db, user_id=current_user.id
    )
    return enrollments


@router.get("/{course_id}", response_model=CourseWithModules)
def get_course(course_id: int, db: Session = Depends(deps.get_db)) -> Any:
    """
    Get course details with modules and lessons
    """
    course = crud_course.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put("/{course_id}", response_model=CourseSchema)
def update_course(
    course_id: int,
    *,
    db: Session = Depends(deps.get_db),
    course_in: CourseUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a course (instructor only)
    """
    course = crud_course.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if user is the instructor
    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this course"
        )

    course = crud_course.course.update(db=db, db_obj=course, obj_in=course_in)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete a course (instructor only)
    """
    course = crud_course.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if user is the instructor
    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this course"
        )

    crud_course.course.remove(db=db, id=course_id)


@router.get("/{course_id}/modules", response_model=List[ModuleWithLessons])
def get_course_modules(course_id: int, db: Session = Depends(deps.get_db)) -> Any:
    """
    Get all modules for a course
    """
    modules = crud_course.module.get_by_course(db=db, course_id=course_id)
    return modules


# ============================================================================
# MODULE ENDPOINTS
# ============================================================================


@router.post(
    "/{course_id}/modules",
    response_model=ModuleSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_module(
    course_id: int,
    *,
    db: Session = Depends(deps.get_db),
    module_in: ModuleCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Add a module to a course (instructor only)
    """
    course = crud_course.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    module = crud_course.module.create_with_course(
        db=db, obj_in=module_in, course_id=course_id
    )
    return module


@modules_router.put("/{module_id}", response_model=ModuleSchema)
def update_module(
    module_id: int,
    *,
    db: Session = Depends(deps.get_db),
    module_in: ModuleUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a module (instructor only)
    """
    module = crud_course.module.get(db=db, id=module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    course = crud_course.course.get(db=db, id=module.course_id)
    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    module = crud_course.module.update(db=db, db_obj=module, obj_in=module_in)
    return module


@modules_router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(
    module_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete a module (instructor only)
    """
    module = crud_course.module.get(db=db, id=module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    course = crud_course.course.get(db=db, id=module.course_id)
    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    crud_course.module.remove(db=db, id=module_id)


@router.post("/{course_id}/reorder-modules")
def reorder_modules(
    course_id: int,
    *,
    db: Session = Depends(deps.get_db),
    module_ids: List[int],
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Reorder modules in a course (instructor only)
    """
    course = crud_course.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update order_index for each module
    for index, module_id in enumerate(module_ids):
        module = crud_course.module.get(db=db, id=module_id)
        if module and module.course_id == course_id:
            module.order_index = index

    db.commit()
    return {"message": "Modules reordered successfully"}


@modules_router.post("/{module_id}/reorder-lessons")
def reorder_lessons(
    module_id: int,
    *,
    db: Session = Depends(deps.get_db),
    lesson_ids: List[int],
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Reorder lessons in a module (instructor only)
    """
    module = crud_course.module.get(db=db, id=module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    course = crud_course.course.get(db=db, id=module.course_id)
    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update order_index for each lesson
    for index, lesson_id in enumerate(lesson_ids):
        lesson = crud_course.lesson.get(db=db, id=lesson_id)
        if lesson and lesson.module_id == module_id:
            lesson.order_index = index

    db.commit()
    return {"message": "Lessons reordered successfully"}


# ============================================================================
# LESSON ENDPOINTS
# ============================================================================


@modules_router.post(
    "/{module_id}/lessons",
    response_model=LessonSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    module_id: int,
    *,
    db: Session = Depends(deps.get_db),
    lesson_in: LessonCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Add a lesson to a module (instructor only)
    """
    module = crud_course.module.get(db=db, id=module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    course = crud_course.course.get(db=db, id=module.course_id)
    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    lesson = crud_course.lesson.create_with_module(
        db=db, obj_in=lesson_in, module_id=module_id
    )
    return lesson


@lessons_router.put("/{lesson_id}", response_model=LessonSchema)
def update_lesson(
    lesson_id: int,
    *,
    db: Session = Depends(deps.get_db),
    lesson_in: LessonUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a lesson (instructor only)
    """
    lesson = crud_course.lesson.get(db=db, id=lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    module = crud_course.module.get(db=db, id=lesson.module_id)
    course = crud_course.course.get(db=db, id=module.course_id)

    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    lesson = crud_course.lesson.update(db=db, db_obj=lesson, obj_in=lesson_in)
    return lesson


@lessons_router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """
    Delete a lesson (instructor only)
    """
    lesson = crud_course.lesson.get(db=db, id=lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    module = crud_course.module.get(db=db, id=lesson.module_id)
    course = crud_course.course.get(db=db, id=module.course_id)

    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    crud_course.lesson.remove(db=db, id=lesson_id)


# ============================================================================
# ENROLLMENT ENDPOINTS
# ============================================================================


@router.post(
    "/{course_id}/enroll",
    response_model=EnrollmentSchema,
    status_code=status.HTTP_201_CREATED,
)
def enroll_in_course(
    course_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    password_data: Optional[dict] = None,
) -> Any:
    """
    Enroll current user in a course
    """
    course = crud_course.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if already enrolled
    existing = crud_enrollment.get_enrollment(
        db=db, course_id=course_id, student_id=current_user.id
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    # Check password if protected
    if course.is_password_protected:
        from app.core.security import verify_password

        provided_password = password_data.get("password") if password_data else None
        if not provided_password:
            raise HTTPException(
                status_code=403, detail="Password required for this course"
            )

        if not verify_password(provided_password, course.password_hash):
            raise HTTPException(status_code=403, detail="Invalid course password")

    enrollment = crud_enrollment.create_enrollment(
        db=db, user_id=current_user.id, course_id=course_id
    )

    # Create notification for enrollment
    from app.services.notification_helpers import create_and_emit_notification
    from app.models.notification import NotificationType

    create_and_emit_notification(
        db=db,
        user_id=current_user.id,
        notification_type=NotificationType.COURSE_ENROLLED,
        title="Course Enrollment",
        message=f"You successfully enrolled in {course.title}",
        data={"course_id": course.id, "course_name": course.title},
        action_url=f"/lms/courses/{course.id}",
    )

    # Send enrollment email
    try:
        from app.services.email_notification_service import send_enrollment_email_sync

        send_enrollment_email_sync(db, current_user, course)
    except Exception as e:
        # Log error but don't fail enrollment if email fails
        print(f"Failed to send enrollment email: {e}")

    # Award coins for course enrollment
    try:
        from app.services.coin_service import trigger_coin_reward

        trigger_coin_reward(
            db=db,
            user=current_user,
            action="course_enroll",
            reference_type="course",
            reference_id=course.id,
            description=f"Enrolled in: {course.title}",
        )
    except Exception as e:
        print(f"Failed to award coins for enrollment: {e}")

    return enrollment


@router.get("/{course_id}/export", response_model=dict)
def export_course(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Export a course as JSON
    """
    course = crud_course.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not crud_course.course.is_active(course) and not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Inactive course")

    # Check permissions
    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Serialize manually to ensure deep structure
    from app.schemas.course_export import CourseExport

    return CourseExport.from_orm(course).model_dump()


@router.post("/import", response_model=CourseSchema)
def import_course(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Import a course from JSON file
    """
    if not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=400, detail="Invalid file format. Please upload a JSON file."
        )

    import json

    try:
        content = file.file.read()
        course_data = json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")

    # Create course from import
    course = crud_course.course.create_from_import(
        db=db, obj_in=course_data, instructor_id=current_user.id
    )

    return course


@router.get("/{course_id}/export", response_model=dict)
def export_course(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Export a course as JSON
    """
    course = crud_course.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not crud_course.course.is_active(course) and not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Inactive course")

    # Check permissions
    if course.instructor_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Serialize manually to ensure deep structure
    from app.schemas.course_export import CourseExport

    return CourseExport.from_orm(course).model_dump()


@router.post("/import", response_model=CourseSchema)
def import_course(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Import a course from JSON file
    """
    if not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=400, detail="Invalid file format. Please upload a JSON file."
        )

    import json

    try:
        content = file.file.read()
        course_data = json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")

    # Create course from import
    course = crud_course.course.create_from_import(
        db=db, obj_in=course_data, instructor_id=current_user.id
    )

    return course


@router.get("/{course_id}/progress")
def get_course_progress(
    course_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get user's progress in a course
    """
    enrollment = crud_enrollment.get_enrollment(
        db=db, course_id=course_id, student_id=current_user.id
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")

    return {
        "course_id": course_id,
        "progress_percentage": enrollment.progress_percentage,
        "last_accessed_lesson_id": enrollment.last_accessed_lesson_id,
        "enrolled_at": enrollment.enrolled_at,
        "last_accessed_at": enrollment.last_accessed_at,
    }


# ============================================================================
# REVIEW ENDPOINTS
# ============================================================================


@router.post(
    "/{course_id}/reviews",
    response_model=CourseReviewSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    course_id: int,
    *,
    db: Session = Depends(deps.get_db),
    review_in: CourseReviewCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a review for a course (must be enrolled)
    """
    # Check if enrolled
    if not crud_enrollment.get_enrollment(
        db=db, course_id=course_id, student_id=current_user.id
    ):
        raise HTTPException(status_code=403, detail="Must be enrolled to review")

    review = crud_course.course_review.create(
        db=db, obj_in=review_in, user_id=current_user.id
    )
    db.refresh(review)

    # Award coins for writing a review!
    try:
        from app.services.coin_service import trigger_coin_reward

        trigger_coin_reward(
            db=db,
            user=current_user,
            action="review_write",
            reference_type="course",
            reference_id=course_id,
            description=f"Reviewed course: {review.course.title if review.course else 'Unknown'}",
        )
    except Exception as e:
        print(f"Failed to award coins for review: {e}")

    # Convert to schema and populate author_name
    result = CourseReviewSchema.from_orm(review)
    if review.user:
        result.author_name = review.user.full_name

    return result


@router.get("/{course_id}/reviews", response_model=List[CourseReviewSchema])
def get_course_reviews(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional),
) -> Any:
    """
    Get all reviews for a course
    """
    reviews = (
        db.query(CourseReview)
        .filter(CourseReview.course_id == course_id, CourseReview.is_approved == 1)
        .order_by(CourseReview.created_at.desc())
        .all()
    )

    # If user is logged in, check which reviews they found helpful
    helpful_review_ids = set()
    if current_user:
        helpful_votes = (
            db.query(ReviewHelpful.review_id)
            .filter(
                ReviewHelpful.user_id == current_user.id,
                ReviewHelpful.review_id.in_([r.id for r in reviews]),
            )
            .all()
        )
        helpful_review_ids = {h[0] for h in helpful_votes}

    # Enrich reviews with author name and helpful status
    result = []
    for review in reviews:
        # We need to ensure the schema can handle author_name if it's not in the model
        # The schema CourseReviewInDBBase doesn't have author_name.
        # But the frontend expects it.
        # We might need to update the schema or use a custom response.
        # For now, let's assume the schema will be updated or we map it.

        review_data = CourseReviewSchema.from_orm(review)
        if current_user:
            review_data.has_found_helpful = review.id in helpful_review_ids

        if review.user:
            review_data.author_name = review.user.full_name

        result.append(review_data)

    return result


@router.get("/{course_id}/reviews/breakdown")
def get_reviews_breakdown(course_id: int, db: Session = Depends(deps.get_db)) -> Any:
    """
    Get ratings breakdown for a course
    """
    reviews = (
        db.query(CourseReview)
        .filter(CourseReview.course_id == course_id, CourseReview.is_approved == 1)
        .all()
    )

    total_reviews = len(reviews)
    if total_reviews == 0:
        return {
            "average_rating": 0,
            "total_reviews": 0,
            "ratings": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0},
        }

    total_rating = sum(r.rating for r in reviews)
    average_rating = total_rating / total_reviews

    ratings_count = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in reviews:
        rating = int(round(r.rating))
        if rating in ratings_count:
            ratings_count[rating] += 1

    return {
        "average_rating": average_rating,
        "total_reviews": total_reviews,
        "ratings": ratings_count,
    }


@router.get(
    "/{course_id}/reviews/my-review", response_model=Optional[CourseReviewSchema]
)
def get_my_review(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get the current user's review for this course
    """
    review = (
        db.query(CourseReview)
        .filter(
            CourseReview.course_id == course_id, CourseReview.user_id == current_user.id
        )
        .first()
    )

    return review
