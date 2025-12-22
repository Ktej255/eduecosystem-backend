from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, timezone
from app.models.learning_path import LearningPath, PathCourse, PathEnrollment
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas import learning_path as schemas


# LearningPath CRUD
def create_learning_path(
    db: Session, path: schemas.LearningPathCreate, creator_id: int
) -> LearningPath:
    """Create a new learning path"""
    # Generate slug from title if not provided
    if not path.slug:
        slug_base = path.title.lower().replace(" ", "-")
        path.slug = slug_base

    db_path = LearningPath(**path.model_dump(), creator_id=creator_id)
    db.add(db_path)
    db.commit()
    db.refresh(db_path)
    return db_path


def get_learning_path(db: Session, path_id: int) -> Optional[LearningPath]:
    """Get a learning path by ID"""
    return db.query(LearningPath).filter(LearningPath.id == path_id).first()


def get_learning_path_by_slug(db: Session, slug: str) -> Optional[LearningPath]:
    """Get a learning path by slug"""
    return db.query(LearningPath).filter(LearningPath.slug == slug).first()


def get_learning_paths(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    published_only: bool = True,
    difficulty: Optional[str] = None,
) -> List[LearningPath]:
    """Get all learning paths with optional filters"""
    query = db.query(LearningPath)

    if published_only:
        query = query.filter(LearningPath.is_published == True)

    if difficulty:
        query = query.filter(LearningPath.difficulty_level == difficulty)

    return (
        query.order_by(LearningPath.created_at.desc()).offset(skip).limit(limit).all()
    )


def update_learning_path(
    db: Session, path_id: int, path_update: schemas.LearningPathUpdate
) -> Optional[LearningPath]:
    """Update a learning path"""
    db_path = get_learning_path(db, path_id)
    if not db_path:
        return None

    update_data = path_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_path, field, value)

    db.commit()
    db.refresh(db_path)
    return db_path


def delete_learning_path(db: Session, path_id: int) -> bool:
    """Delete a learning path"""
    db_path = get_learning_path(db, path_id)
    if not db_path:
        return False

    db.delete(db_path)
    db.commit()
    return True


# PathCourse CRUD
def add_course_to_path(
    db: Session, path_course: schemas.PathCourseCreate
) -> PathCourse:
    """Add a course to a learning path"""
    db_path_course = PathCourse(**path_course.model_dump())
    db.add(db_path_course)

    # Update total courses count for existing enrollments
    enrollments = (
        db.query(PathEnrollment)
        .filter(PathEnrollment.path_id == path_course.path_id)
        .all()
    )

    for enrollment in enrollments:
        enrollment.total_courses += 1
        enrollment.progress_percentage = (
            enrollment.completed_courses / enrollment.total_courses
        ) * 100

    db.commit()
    db.refresh(db_path_course)
    return db_path_course


def get_path_courses(db: Session, path_id: int) -> List[PathCourse]:
    """Get all courses in a learning path"""
    return (
        db.query(PathCourse)
        .filter(PathCourse.path_id == path_id)
        .order_by(PathCourse.order_index)
        .all()
    )


def get_path_course(db: Session, path_course_id: int) -> Optional[PathCourse]:
    """Get a specific path course"""
    return db.query(PathCourse).filter(PathCourse.id == path_course_id).first()


def update_path_course(
    db: Session, path_course_id: int, path_course_update: schemas.PathCourseUpdate
) -> Optional[PathCourse]:
    """Update a path course"""
    db_path_course = (
        db.query(PathCourse).filter(PathCourse.id == path_course_id).first()
    )
    if not db_path_course:
        return None

    update_data = path_course_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_path_course, field, value)

    db.commit()
    db.refresh(db_path_course)
    return db_path_course


def remove_course_from_path(db: Session, path_course_id: int) -> bool:
    """Remove a course from a learning path"""
    db_path_course = (
        db.query(PathCourse).filter(PathCourse.id == path_course_id).first()
    )
    if not db_path_course:
        return False

    path_id = db_path_course.path_id
    db.delete(db_path_course)

    # Update total courses count for existing enrollments
    enrollments = (
        db.query(PathEnrollment).filter(PathEnrollment.path_id == path_id).all()
    )

    for enrollment in enrollments:
        enrollment.total_courses -= 1
        if enrollment.total_courses > 0:
            enrollment.progress_percentage = (
                enrollment.completed_courses / enrollment.total_courses
            ) * 100

    db.commit()
    return True


# PathEnrollment CRUD
def enroll_in_path(db: Session, path_id: int, student_id: int) -> PathEnrollment:
    """Enroll a student in a learning path"""
    # Check if already enrolled
    existing = (
        db.query(PathEnrollment)
        .filter(
            and_(
                PathEnrollment.path_id == path_id,
                PathEnrollment.student_id == student_id,
            )
        )
        .first()
    )

    if existing:
        return existing

    # Get total courses
    total_courses = (
        db.query(func.count(PathCourse.id))
        .filter(PathCourse.path_id == path_id)
        .scalar()
    )

    enrollment = PathEnrollment(
        path_id=path_id,
        student_id=student_id,
        total_courses=total_courses or 0,
        has_paid=True,  # TODO: Integrate with payment system
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def get_student_path_enrollments(db: Session, student_id: int) -> List[PathEnrollment]:
    """Get all path enrollments for a student"""
    from sqlalchemy.orm import joinedload

    return (
        db.query(PathEnrollment)
        .options(joinedload(PathEnrollment.path))
        .filter(PathEnrollment.student_id == student_id)
        .all()
    )


def get_path_enrollment(
    db: Session, path_id: int, student_id: int
) -> Optional[PathEnrollment]:
    """Get a specific path enrollment"""
    return (
        db.query(PathEnrollment)
        .filter(
            and_(
                PathEnrollment.path_id == path_id,
                PathEnrollment.student_id == student_id,
            )
        )
        .first()
    )


def update_path_enrollment_progress(
    db: Session, enrollment_id: int, completed_course_id: int
) -> Optional[PathEnrollment]:
    """Update enrollment progress when a course is completed"""
    enrollment = (
        db.query(PathEnrollment).filter(PathEnrollment.id == enrollment_id).first()
    )
    if not enrollment:
        return None

    enrollment.completed_courses += 1
    enrollment.last_accessed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    if enrollment.total_courses > 0:
        enrollment.progress_percentage = (
            enrollment.completed_courses / enrollment.total_courses
        ) * 100

    # Check if path is completed
    if enrollment.completed_courses >= enrollment.total_courses:
        enrollment.is_completed = True
        enrollment.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    else:
        # Find next course
        path_courses = get_path_courses(db, enrollment.path_id)
        for i, pc in enumerate(path_courses):
            if pc.course_id == completed_course_id and i + 1 < len(path_courses):
                enrollment.current_course_id = path_courses[i + 1].course_id
                break

    db.commit()
    db.refresh(enrollment)
    return enrollment


def check_course_access(
    db: Session, path_id: int, student_id: int, course_id: int
) -> bool:
    """Check if student has access to a course in the path"""
    enrollment = get_path_enrollment(db, path_id, student_id)
    if not enrollment:
        return False

    # Get course info
    path_course = (
        db.query(PathCourse)
        .filter(and_(PathCourse.path_id == path_id, PathCourse.course_id == course_id))
        .first()
    )

    if not path_course:
        return False

    # If no prerequisite, allow access
    if not path_course.prerequisite_course_id:
        return True

    # Check if prerequisite is completed
    prereq_enrollment = (
        db.query(Enrollment)
        .filter(
            and_(
                Enrollment.user_id == student_id,
                Enrollment.course_id == path_course.prerequisite_course_id,
                Enrollment.status == EnrollmentStatus.COMPLETED,
            )
        )
        .first()
    )

    return prereq_enrollment is not None
