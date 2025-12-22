from typing import Any, List, Optional
import uuid
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models.upsc import (
    UPSCBatch, UPSCPlan, UPSCQuestion, UPSCContent, UPSCDrill, 
    UPSCAttempt, UPSCReport, UPSCStudentProgress
)
from app.services.upsc_worker import generate_ai_plan_task, analyze_answer_task
from app.schemas.upsc import (
    UPSCBatchCreate, UPSCBatchUpdate, UPSCBatch as UPSCBatchSchema,
    UPSCPlanCreate, UPSCPlanUpdate, UPSCPlan as UPSCPlanSchema,
    UPSCQuestionCreate, UPSCQuestionUpdate, UPSCQuestion as UPSCQuestionSchema,
    UPSCContentCreate, UPSCContent as UPSCContentSchema,
    UPSCAttemptCreate, UPSCAttempt as UPSCAttemptSchema,
    UPSCReport as UPSCReportSchema,
    PlanGenerationRequest, StartDrillRequest, StartDrillResponse,
    StudentDashboardResponse, PlanStatusResponse
)

router = APIRouter()

# --- Admin: Batches ---
@router.post("/batches", response_model=UPSCBatchSchema)
def create_batch(
    *,
    db: Session = Depends(deps.get_db),
    batch_in: UPSCBatchCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new UPSC batch.
    """
    batch = UPSCBatch(
        **batch_in.dict(),
        created_by_id=current_user.id
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch

@router.get("/batches", response_model=List[UPSCBatchSchema])
def read_batches(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve batches.
    """
    batches = db.query(UPSCBatch).offset(skip).limit(limit).all()
    return batches

# --- Admin: Plans ---
@router.post("/plans/generate", status_code=202)
def generate_ai_plan(
    *,
    db: Session = Depends(deps.get_db),
    request: PlanGenerationRequest,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Trigger AI to generate a monthly plan (Async).
    """
    task = generate_ai_plan_task.delay(request.dict())
    return {"message": "Plan generation started", "task_id": str(task.id)}

@router.get("/plans/{batch_id}", response_model=List[UPSCPlanSchema])
def read_plans(
    *,
    db: Session = Depends(deps.get_db),
    batch_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get plans for a batch (Hierarchy).
    """
    plans = db.query(UPSCPlan).filter(UPSCPlan.batch_id == batch_id).all()
    return plans

@router.post("/plans/{plan_id}/approve", response_model=UPSCPlanSchema)
def approve_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Approve an AI-generated plan.
    """
    plan = db.query(UPSCPlan).filter(UPSCPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan.approved_by_id = current_user.id
    plan.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)

    # Trigger Progress Initialization
    from app.services.upsc_worker import initialize_student_progress_task
    initialize_student_progress_task.delay(str(plan.id))

    return plan

# --- Admin: Questions & Content ---
@router.post("/questions", response_model=UPSCQuestionSchema)
def create_question(
    *,
    db: Session = Depends(deps.get_db),
    question_in: UPSCQuestionCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create a new question manually.
    """
    question = UPSCQuestion(
        **question_in.dict(),
        created_by_id=current_user.id
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question

@router.post("/content", response_model=UPSCContentSchema)
def create_content(
    *,
    db: Session = Depends(deps.get_db),
    content_in: UPSCContentCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Add content (one-pager, model answer) to a question.
    """
    content = UPSCContent(
        **content_in.dict(),
        created_by_id=current_user.id
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return content

# --- Student: Drill Workflow ---
@router.post("/drills/start", response_model=StartDrillResponse)
def start_drill_session(
    *,
    db: Session = Depends(deps.get_db),
    request: StartDrillRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Start a drill session for a specific question.
    """
    # 1. Verify Plan & Question exist
    question = db.query(UPSCQuestion).filter(
        UPSCQuestion.plan_id == request.plan_id,
        UPSCQuestion.question_number == request.question_number
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # 2. Create or Get Drill Session (Logic simplified for now)
    session_id = uuid.uuid4() # Placeholder for actual session logic

    # 3. Return initial state
    return {
        "session_id": session_id,
        "question": question,
        "current_step": {"step": "read", "duration": 300},
        "timer_config": {"read": 300, "write_before": 1200, "study": 3600, "write_after": 1200}
    }

@router.post("/attempts", response_model=UPSCAttemptSchema)
def submit_attempt(
    *,
    db: Session = Depends(deps.get_db),
    question_id: UUID = Form(...),
    attempt_type: str = Form(...),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Submit an answer attempt (Image or Audio upload).
    """
    if not image and not audio:
        raise HTTPException(status_code=400, detail="Either image or audio must be provided")

    image_url = None
    audio_url = None

    if image:
        # TODO: Upload to S3
        image_url = f"https://s3-bucket/placeholder/{image.filename}"
    
    if audio:
        # TODO: Upload to S3
        # For now, save locally for testing or mock URL
        import shutil
        import os
        upload_dir = "uploads/audio"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = f"{upload_dir}/{uuid.uuid4()}_{audio.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        audio_url = file_path # In real app, this would be S3 URL

    attempt = UPSCAttempt(
        student_id=current_user.id,
        question_id=question_id,
        attempt_type=attempt_type,
        image_url=image_url,
        audio_url=audio_url,
        # ocr_text/transcription will be populated by worker
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    # Trigger Background Tasks
    if image:
        analyze_answer_task.delay(str(attempt.id))
    
    if audio:
        # We need to import this task, assuming it will be in upsc_worker
        from app.services.upsc_worker import transcribe_audio_task
        transcribe_audio_task.delay(str(attempt.id), file_path) # Passing path for now
    
    return attempt

@router.get("/reports/{report_id}", response_model=UPSCReportSchema)
def get_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get AI analysis report.
    """
    report = db.query(UPSCReport).filter(UPSCReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.student_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    return report

@router.get("/student/dashboard", response_model=StudentDashboardResponse)
def get_student_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get student dashboard data.
    """
    # 1. Calculate total days completed
    completed_days = db.query(UPSCStudentProgress).filter(
        UPSCStudentProgress.student_id == current_user.id,
        UPSCStudentProgress.completion_percentage == 100.0
    ).count()

    # 2. Get recent reports
    recent_reports = db.query(UPSCReport).filter(
        UPSCReport.student_id == current_user.id
    ).order_by(UPSCReport.generated_at.desc()).limit(5).all()

    # 3. Determine next drill (simplified logic)
    # Find the first unlocked but incomplete plan
    next_plan_progress = db.query(UPSCStudentProgress).filter(
        UPSCStudentProgress.student_id == current_user.id,
        UPSCStudentProgress.is_locked == False,
        UPSCStudentProgress.completion_percentage < 100.0
    ).first()

    next_drill = None
    if next_plan_progress:
        plan = db.query(UPSCPlan).filter(UPSCPlan.id == next_plan_progress.plan_id).first()
        if plan:
            next_drill = {
                "plan_id": plan.id,
                "title": plan.title,
                "type": plan.plan_type
            }

    dashboard_data = {
        "total_days_completed": completed_days,
        "current_streak": 0, # Placeholder
        "next_drill": next_drill,
        "recent_reports": recent_reports
    }
    return dashboard_data

@router.get("/student/plans", response_model=List[UPSCPlanSchema])
def get_student_plans(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get plans available to the student.
    """
    # Get student's batch
    # Assuming student profile exists and links to batch
    # For now, we'll fetch all plans for the batch the user is enrolled in
    # This requires a way to link user to batch. 
    # Let's assume we have a way, or just return all plans for now if user is admin/student
    
    # TODO: Fetch from student profile
    # profile = db.query(UPSCStudentProfile).filter(UPSCStudentProfile.user_id == current_user.id).first()
    # if not profile: return []
    # batch_id = profile.batch_id
    
    # Fallback: Get first batch for demo
    batch = db.query(UPSCBatch).first()
    if not batch:
        return []
        
    plans = db.query(UPSCPlan).filter(UPSCPlan.batch_id == batch.id).all()
    return plans

@router.get("/student/plans/{plan_id}/status", response_model=PlanStatusResponse)
def get_plan_status(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get lock/unlock status for a plan.
    """
    progress = db.query(UPSCStudentProgress).filter(
        UPSCStudentProgress.student_id == current_user.id,
        UPSCStudentProgress.plan_id == plan_id
    ).first()

    if not progress:
        # Default to locked if no progress record exists
        return {
            "plan_id": plan_id,
            "is_locked": True,
            "completion_percentage": 0.0
        }
    
    return progress

# Admin Override Endpoints - append to upsc.py

# --- Admin: Progress Override ---
@router.post("/admin/progress/override", response_model=PlanStatusResponse)
def override_student_progress(
    *,
    db: Session = Depends(deps.get_db),
    student_id: int,
    plan_id: UUID,
    is_locked: bool,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Admin override: Manually lock or unlock a plan for a specific student.
    """
    progress = db.query(UPSCStudentProgress).filter(
        UPSCStudentProgress.student_id == student_id,
        UPSCStudentProgress.plan_id == plan_id
    ).first()
    
    if not progress:
        raise HTTPException(
            status_code=404,
            detail="Student progress record not found"
        )
    
    progress.is_locked = is_locked
    if not is_locked and not progress.unlocked_at:
        progress.unlocked_at = datetime.utcnow()
    
    db.commit()
    db.refresh(progress)
    
    return PlanStatusResponse(
        plan_id=str(progress.plan_id),
        is_locked=progress.is_locked,
        completion_percentage=float(progress.completion_percentage),
        unlocked_at=progress.unlocked_at,
        completed_at=progress.completed_at
    )


# --- Admin: Get Students by Batch ---
@router.get("/admin/batches/{batch_id}/students")
def get_batch_students(
    *,
    db: Session = Depends(deps.get_db),
    batch_id: UUID,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get all students enrolled in a batch with their progress.
    """
    from app.models.upsc import UPSCStudentProfile
    from app.models.user import User
    
    profiles = db.query(UPSCStudentProfile).filter(
        UPSCStudentProfile.batch_id == batch_id
    ).all()
    
    students = []
    for profile in profiles:
        user = db.query(User).filter(User.id == profile.user_id).first()
        if user:
            # Get progress summary
            progress_count = db.query(UPSCStudentProgress).filter(
                UPSCStudentProgress.student_id == user.id
            ).count()
            
            students.append({
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "enrollment_date": profile.enrollment_date,
                "target_year": profile.target_year,
                "progress_records": progress_count
            })
    
    return students


# --- Admin: Get Student Progress Detail ---
@router.get("/admin/students/{student_id}/progress")
def get_student_progress(
    *,
    db: Session = Depends(deps.get_db),
    student_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get detailed progress for a specific student across all plans.
    """
    progress_records = db.query(UPSCStudentProgress).filter(
        UPSCStudentProgress.student_id == student_id
    ).all()
    
    result = []
    for prog in progress_records:
        plan = db.query(UPSCPlan).filter(UPSCPlan.id == prog.plan_id).first()
        if plan:
            result.append({
                "plan_id": str(plan.id),
                "plan_title": plan.title,
                "plan_type": plan.plan_type,
                "is_locked": prog.is_locked,
                "completion_percentage": float(prog.completion_percentage),
                "unlocked_at": prog.unlocked_at,
                "completed_at": prog.completed_at
            })
    
    return result
