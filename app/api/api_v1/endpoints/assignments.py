from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import os
import uuid

from app.api import deps
from app.models.user import User
from app.models.assignment import Assignment, Submission, SubmissionStatus
from app.schemas.assignment import (
    Assignment as AssignmentSchema,
    AssignmentCreate,
    AssignmentUpdate,
    Submission as SubmissionSchema,
    SubmissionUpdate,
    SubmissionWithUser,
)

router = APIRouter()

# ============================================================================
# ASSIGNMENT ENDPOINTS
# ============================================================================


@router.post("/", response_model=AssignmentSchema)
def create_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assignment_in: AssignmentCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new assignment (instructor only)
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    db_assignment = Assignment(**assignment_in.model_dump())
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment


@router.get("/{assignment_id}", response_model=AssignmentSchema)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get assignment details
    """
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.put("/{assignment_id}", response_model=AssignmentSchema)
def update_assignment(
    assignment_id: int,
    *,
    db: Session = Depends(deps.get_db),
    assignment_in: AssignmentUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update assignment (instructor only)
    """
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = assignment_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)

    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/course/{course_id}", response_model=List[AssignmentSchema])
def list_course_assignments(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    List all assignments for a course
    """
    assignments = db.query(Assignment).filter(Assignment.course_id == course_id).all()
    return assignments


# ============================================================================
# SUBMISSION ENDPOINTS
# ============================================================================


@router.post("/{assignment_id}/submit", response_model=SubmissionSchema)
async def submit_assignment(
    assignment_id: int,
    *,
    db: Session = Depends(deps.get_db),
    files: List[UploadFile] = File(default=[]),
    notes: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Submit an assignment with file uploads
    """
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check if submission already exists
    existing_submission = (
        db.query(Submission)
        .filter(
            Submission.assignment_id == assignment_id,
            Submission.user_id == current_user.id,
        )
        .first()
    )

    # Upload files
    uploaded_files = []
    upload_dir = f"uploads/assignments/{assignment_id}"
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        uploaded_files.append(file_path)

    # Calculate status (check if late)
    status = SubmissionStatus.SUBMITTED
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # Naive UTC for SQLite

    # Compare naive datetimes (SQLite stores as naive)
    if assignment.due_date:
        if now > assignment.due_date:
            status = SubmissionStatus.LATE

    if existing_submission:
        # Update existing submission
        existing_submission.submitted_files = uploaded_files
        existing_submission.notes = notes
        existing_submission.status = status
        existing_submission.submitted_at = now
        db.add(existing_submission)
        db.commit()
        db.refresh(existing_submission)

        # Notify instructor of resubmission
        try:
            from app.services.email_notification_service import (
                send_assignment_submitted_email_sync,
            )

            instructor = (
                db.query(User).filter(User.id == assignment.instructor_id).first()
            )
            if instructor:
                send_assignment_submitted_email_sync(db, instructor, assignment)
        except Exception as e:
            print(f"Failed to send assignment submission email: {e}")

        return existing_submission
    else:
        # Create new submission
        db_submission = Submission(
            assignment_id=assignment_id,
            user_id=current_user.id,
            submitted_files=uploaded_files,
            notes=notes,
            status=status,
            submitted_at=now,
        )
        db.add(db_submission)
        db.commit()
        db.refresh(db_submission)

        # Notify instructor of new submission
        try:
            from app.services.email_notification_service import (
                send_assignment_submitted_email_sync,
            )

            instructor = (
                db.query(User).filter(User.id == assignment.instructor_id).first()
            )
            if instructor:
                send_assignment_submitted_email_sync(db, instructor, assignment)
        except Exception as e:
            print(f"Failed to send assignment submission email: {e}")

        # Award coins for submitting assignment
        try:
            from app.services.coin_service import trigger_coin_reward

            trigger_coin_reward(
                db=db,
                user=current_user,
                action="assignment_submit",
                reference_type="assignment",
                reference_id=assignment.id,
                description=f"Submitted: {assignment.title}",
            )
        except Exception as e:
            print(f"Failed to award coins for assignment submission: {e}")

        return db_submission


@router.post(
    "/{assignment_id}/submissions/{submission_id}/grade",
    response_model=SubmissionSchema,
)
def grade_submission(
    assignment_id: int,
    submission_id: int,
    *,
    db: Session = Depends(deps.get_db),
    grade_data: SubmissionUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Grade a student's submission (instructor only)
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Apply late penalty if applicable
    final_grade = grade_data.grade if grade_data.grade is not None else 0
    if (
        submission.status == SubmissionStatus.LATE
        and assignment.late_penalty_per_day > 0
    ):
        # All datetimes from SQLite are naive
        submitted_at = submission.submitted_at
        due_date = assignment.due_date

        if submitted_at and due_date:
            days_late = (submitted_at - due_date).days
            penalty = (assignment.late_penalty_per_day / 100) * final_grade * days_late
            final_grade = max(0, final_grade - penalty)

    submission.grade = final_grade
    submission.feedback = grade_data.feedback
    submission.status = SubmissionStatus.GRADED
    submission.graded_at = datetime.now(timezone.utc).replace(
        tzinfo=None
    )  # Naive UTC for SQLite

    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Send grading email to student
    try:
        from app.services.email_notification_service import (
            send_assignment_graded_email_sync,
        )

        student = db.query(User).filter(User.id == submission.student_id).first()
        if student:
            send_assignment_graded_email_sync(db, student, assignment, final_grade)
    except Exception as e:
        # Log error but don't fail grading if email fails
        print(f"Failed to send grading email: {e}")

    # Award coins based on grade!
    try:
        from app.services.coin_service import trigger_coin_reward

        student = db.query(User).filter(User.id == submission.user_id).first()

        if student and final_grade is not None:
            # Calculate percentage (assuming max_grade is 100)
            max_grade = assignment.max_grade if assignment.max_grade else 100
            percentage = (final_grade / max_grade) * 100 if max_grade > 0 else 0

            # Award based on grade level
            if percentage >= 90:  # A grade
                trigger_coin_reward(
                    db=db,
                    user=student,
                    action="assignment_a_grade",
                    reference_type="assignment",
                    reference_id=assignment.id,
                    description=f"A grade on: {assignment.title}",
                )
            elif percentage >= 80:  # B grade
                trigger_coin_reward(
                    db=db,
                    user=student,
                    action="assignment_b_grade",
                    reference_type="assignment",
                    reference_id=assignment.id,
                    description=f"B grade on: {assignment.title}",
                )
    except Exception as e:
        # Log error but don't fail grading if coin awarding fails
        print(f"Failed to award coins for assignment grade: {e}")

    return submission


@router.get("/{assignment_id}/submissions", response_model=List[SubmissionWithUser])
def list_submissions(
    assignment_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    List all submissions for an assignment (instructor only)
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    submissions = (
        db.query(Submission).filter(Submission.assignment_id == assignment_id).all()
    )

    # Enhance with user info
    result = []
    for sub in submissions:
        sub_dict = SubmissionWithUser.model_validate(sub).model_dump()
        user = db.query(User).filter(User.id == sub.user_id).first()
        if user:
            sub_dict["user"] = {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
            }
        result.append(sub_dict)

    return result


@router.get("/{assignment_id}/my-submission", response_model=Optional[SubmissionSchema])
def get_my_submission(
    assignment_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's submission for an assignment
    """
    submission = (
        db.query(Submission)
        .filter(
            Submission.assignment_id == assignment_id,
            Submission.user_id == current_user.id,
        )
        .first()
    )

    return submission
