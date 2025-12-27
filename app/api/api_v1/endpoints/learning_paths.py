from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api import deps
from app.crud import learning_path as crud
from app.crud import user as user_crud
from app.schemas import learning_path as schemas
from app.models.user import User

router = APIRouter()


# Learning Path endpoints
@router.post("/", response_model=schemas.LearningPath)
def create_learning_path(
    path: schemas.LearningPathCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Create a new learning path.
    Creator only (instructors/admins).
    """
    # Check permission: only instructors and admins can create learning paths
    if not current_user.is_superuser:
        from app.crud import permissions as crud_permissions

        has_permission = crud_permissions.check_permission(
            db, current_user.id, "create_learning_path"
        )
        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail="Permission denied: create_learning_path required",
            )

    return crud.create_learning_path(db, path, current_user.id)


@router.get("/my-enrollments", response_model=List[schemas.PathEnrollmentWithProgress])
def get_my_path_enrollments(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get all path enrollments for the current user.
    """
    enrollments = crud.get_student_path_enrollments(db, current_user.id)
    return enrollments


@router.get("/", response_model=List[schemas.LearningPath])
def get_learning_paths(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    published_only: bool = True,
    difficulty: Optional[str] = None,
    db: Session = Depends(deps.get_db),
):
    """
    Get all learning paths with optional filters.
    """
    return crud.get_learning_paths(
        db, skip=skip, limit=limit, published_only=published_only, difficulty=difficulty
    )


@router.get("/{path_id}", response_model=schemas.LearningPathWithCourses)
def get_learning_path(path_id: int, db: Session = Depends(deps.get_db)):
    """
    Get a specific learning path by ID with its courses.
    """
    path = crud.get_learning_path(db, path_id)
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Get path courses
    path_courses = crud.get_path_courses(db, path_id)

    # Count enrollments
    from app.models.learning_path import PathEnrollment

    total_enrollments = (
        db.query(PathEnrollment).filter(PathEnrollment.path_id == path_id).count()
    )

    return {
        **path.__dict__,
        "path_courses": path_courses,
        "total_enrollments": total_enrollments,
    }


@router.get("/slug/{slug}", response_model=schemas.LearningPathWithCourses)
def get_learning_path_by_slug(slug: str, db: Session = Depends(deps.get_db)):
    """
    Get a learning path by slug.
    """
    path = crud.get_learning_path_by_slug(db, slug)
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    path_courses = crud.get_path_courses(db, path.id)

    from app.models.learning_path import PathEnrollment

    total_enrollments = (
        db.query(PathEnrollment).filter(PathEnrollment.path_id == path.id).count()
    )

    return {
        **path.__dict__,
        "path_courses": path_courses,
        "total_enrollments": total_enrollments,
    }


@router.put("/{path_id}", response_model=schemas.LearningPath)
def update_learning_path(
    path_id: int,
    path_update: schemas.LearningPathUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update a learning path.
    Creator only.
    """
    db_path = crud.get_learning_path(db, path_id)
    if not db_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Only the creator or superuser can update
    if not current_user.is_superuser and db_path.creator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only the creator can update this learning path"
        )

    updated = crud.update_learning_path(db, path_id, path_update)
    return updated


@router.delete("/{path_id}")
def delete_learning_path(
    path_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Delete a learning path.
    Creator only.
    """
    db_path = crud.get_learning_path(db, path_id)
    if not db_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Only the creator or superuser can delete
    if not current_user.is_superuser and db_path.creator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only the creator can delete this learning path"
        )

    crud.delete_learning_path(db, path_id)
    return {"message": "Learning path deleted successfully"}


# PathCourse endpoints
@router.post("/{path_id}/courses", response_model=schemas.PathCourse)
def add_course_to_path(
    path_id: int,
    path_course: schemas.PathCourseCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Add a course to a learning path.
    Creator only.
    """
    db_path = crud.get_learning_path(db, path_id)
    if not db_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Only the creator or superuser can add courses
    if not current_user.is_superuser and db_path.creator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only the creator can add courses to this path"
        )

    if path_course.path_id != path_id:
        raise HTTPException(status_code=400, detail="Path ID mismatch")

    return crud.add_course_to_path(db, path_course)


@router.get("/{path_id}/courses", response_model=List[schemas.PathCourse])
def get_path_courses(path_id: int, db: Session = Depends(deps.get_db)):
    """
    Get all courses in a learning path.
    """
    return crud.get_path_courses(db, path_id)


@router.put("/courses/{path_course_id}", response_model=schemas.PathCourse)
def update_path_course(
    path_course_id: int,
    path_course_update: schemas.PathCourseUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update a path course (e.g., reorder, change prerequisites).
    Creator only.
    """
    # Get path course to check ownership
    path_course = crud.get_path_course(db, path_course_id)
    if not path_course:
        raise HTTPException(status_code=404, detail="Path course not found")

    # Get the learning path to verify creator
    db_path = crud.get_learning_path(db, path_course.path_id)
    if not db_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Only the creator or superuser can update
    if not current_user.is_superuser and db_path.creator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only the creator can update path courses"
        )

    updated = crud.update_path_course(db, path_course_id, path_course_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Path course not found")

    return updated


@router.delete("/courses/{path_course_id}")
def remove_course_from_path(
    path_course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Remove a course from a learning path.
    Creator only.
    """
    # Get path course to check ownership
    path_course = crud.get_path_course(db, path_course_id)
    if not path_course:
        raise HTTPException(status_code=404, detail="Path course not found")

    # Get the learning path to verify creator
    db_path = crud.get_learning_path(db, path_course.path_id)
    if not db_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Only the creator or superuser can remove
    if not current_user.is_superuser and db_path.creator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only the creator can remove courses from this path"
        )

    success = crud.remove_course_from_path(db, path_course_id)
    if not success:
        raise HTTPException(status_code=404, detail="Path course not found")

    return {"message": "Course removed from path successfully"}


# Enrollment endpoints
@router.post("/{path_id}/enroll", response_model=schemas.PathEnrollment)
def enroll_in_path(
    path_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Enroll the current user in a learning path.
    """
    path = crud.get_learning_path(db, path_id)
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    if not path.is_published:
        raise HTTPException(status_code=400, detail="Learning path is not published")

    # TODO: Check payment if path has a price

    return crud.enroll_in_path(db, path_id, current_user.id)


@router.get("/{path_id}/enrollment", response_model=schemas.PathEnrollment)
def get_path_enrollment(
    path_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get the current user's enrollment in a specific path.
    """
    enrollment = crud.get_path_enrollment(db, path_id, current_user.id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    return enrollment


@router.get("/{path_id}/course/{course_id}/access")
def check_course_access(
    path_id: int,
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Check if the current user has access to a course in the path.
    """
    has_access = crud.check_course_access(db, path_id, current_user.id, course_id)
    return {"has_access": has_access}


@router.post("/{path_id}/assign")
def assign_path_to_student(
    path_id: int,
    email: EmailStr = Body(..., embed=True),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Admin only: Assign a learning path to a student by email.
    """
    # Check if user is admin
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get path
    path = crud.get_learning_path(db, path_id)
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Get student
    student = user_crud.get_user_by_email(db, email=email)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found with this email")

    # Enroll
    return crud.enroll_in_path(db, path_id, student.id)

