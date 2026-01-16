"""
Graphotherapy Progress Tracking Backend
4-Level System with Sequential Day Completion and Image Uploads
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, date
import os
import uuid
import shutil

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.graphotherapy import (
    GraphotherapyProgress, 
    GraphotherapyDayCompletion, 
    GraphoBook,
    GraphoPage,
    GraphoSubmission,
    GRAPHOTHERAPY_LEVELS
)
from app.schemas.graphotherapy import (
    GraphotherapyProgressResponse,
    LevelInfo,
    LevelDetailResponse,
    DayDetailResponse,
    DayCompleteRequest,
    DayCompleteResponse,
    GraphoBookResponse,
    GraphoBookCreate,
    GraphoSubmissionResponse,
    OverviewResponse
)

router = APIRouter()

# Upload directory for graphotherapy images
UPLOAD_DIR = "uploads/graphotherapy"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_or_create_progress(db: Session, user_id: int) -> GraphotherapyProgress:
    """Get existing progress or create new one for user"""
    progress = db.query(GraphotherapyProgress).filter(
        GraphotherapyProgress.user_id == user_id
    ).first()
    
    if not progress:
        progress = GraphotherapyProgress(
            user_id=user_id,
            current_level=1,
            current_day=1,
            total_streak=0
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    return progress


def calculate_streak(progress: GraphotherapyProgress) -> int:
    """Calculate current streak based on last practice date"""
    if not progress.last_practice_date:
        return 0
    
    today = date.today()
    last_practice = progress.last_practice_date.date()
    
    # If practiced today or yesterday, streak is maintained
    if last_practice == today or last_practice == today - timedelta(days=1):
        return progress.total_streak
    else:
        # Streak is broken
        return 0


def is_day_unlocked_by_completion(completion, current_date: date = None) -> bool:
    """
    Check if a completion unlocks the next day.
    The next day is only unlocked if the completion was on a PREVIOUS calendar date.
    This ensures users must wait until midnight (12 AM) for the next day to unlock.
    """
    if completion is None:
        return False
    
    if current_date is None:
        current_date = date.today()
    
    # Get the completion date
    completion_date = completion.completed_at.date()
    
    # Next day is unlocked only if completion was before today (i.e., on a previous day)
    return completion_date < current_date


@router.get("/overview", response_model=OverviewResponse)
def get_graphotherapy_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get overview of graphotherapy progress including all levels"""
    progress = get_or_create_progress(db, current_user.id)
    
    # Get all completions
    completions = db.query(GraphotherapyDayCompletion).filter(
        GraphotherapyDayCompletion.progress_id == progress.id
    ).all()
    
    # Build completion map
    completion_map = {}
    for c in completions:
        if c.level not in completion_map:
            completion_map[c.level] = set()
        completion_map[c.level].add(c.day_number)
    
    # Build level info
    levels = []
    total_completed = 0
    total_remaining = 0
    
    for level_num in range(1, 5):
        level_config = GRAPHOTHERAPY_LEVELS[level_num]
        completed_days = len(completion_map.get(level_num, set()))
        total_days = level_config["days"]
        
        is_unlocked = level_num == 1 or (level_num - 1) in completion_map and len(completion_map[level_num - 1]) >= GRAPHOTHERAPY_LEVELS[level_num - 1]["days"]
        is_current = level_num == progress.current_level
        is_completed = completed_days >= total_days
        
        levels.append(LevelInfo(
            level=level_num,
            name=level_config["name"],
            description=level_config["description"],
            total_days=total_days,
            completed_days=completed_days,
            is_unlocked=is_unlocked,
            is_current=is_current,
            is_completed=is_completed
        ))
        
        total_completed += completed_days
        total_remaining += total_days - completed_days
    
    return OverviewResponse(
        current_level=progress.current_level,
        current_day=progress.current_day,
        total_streak=calculate_streak(progress),
        last_practice_date=progress.last_practice_date,
        levels=levels,
        total_days_completed=total_completed,
        total_days_remaining=total_remaining
    )


@router.get("/level/{level_id}", response_model=LevelDetailResponse)
def get_level_detail(
    level_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get detailed view of a specific level with all days"""
    if level_id not in GRAPHOTHERAPY_LEVELS:
        raise HTTPException(status_code=404, detail="Level not found")
    
    progress = get_or_create_progress(db, current_user.id)
    level_config = GRAPHOTHERAPY_LEVELS[level_id]
    
    # Check if level is unlocked
    if level_id > 1:
        prev_level_config = GRAPHOTHERAPY_LEVELS[level_id - 1]
        prev_completions = db.query(GraphotherapyDayCompletion).filter(
            GraphotherapyDayCompletion.progress_id == progress.id,
            GraphotherapyDayCompletion.level == level_id - 1
        ).count()
        
        if prev_completions < prev_level_config["days"]:
            raise HTTPException(status_code=403, detail="Complete previous level first")
    
    # Get completions for this level
    completions = db.query(GraphotherapyDayCompletion).filter(
        GraphotherapyDayCompletion.progress_id == progress.id,
        GraphotherapyDayCompletion.level == level_id
    ).all()
    
    completion_map = {c.day_number: c for c in completions}
    
    # Build days list
    days = []
    today = date.today()
    for day_num in range(1, level_config["days"] + 1):
        completion = completion_map.get(day_num)
        prev_completion = completion_map.get(day_num - 1) if day_num > 1 else None
        
        # Day is unlocked if:
        # - It's day 1, or
        # - Previous day is completed AND was completed on a PREVIOUS calendar date (not today)
        if day_num == 1:
            is_unlocked = True
        elif prev_completion:
            # Check if previous day was completed before today (unlocks after midnight)
            is_unlocked = is_day_unlocked_by_completion(prev_completion, today)
        else:
            is_unlocked = False
        
        # Calculate unlock date for display
        unlock_date = None
        if not is_unlocked and prev_completion:
            # Will unlock tomorrow (the day after completion)
            unlock_date = (prev_completion.completed_at.date() + timedelta(days=1)).isoformat()
        
        days.append({
            "day_number": day_num,
            "is_unlocked": is_unlocked,
            "is_completed": completion is not None,
            "completed_at": completion.completed_at.isoformat() if completion else None,
            "upload_url": completion.upload_url if completion else None,
            "unlock_date": unlock_date
        })
    
    return LevelDetailResponse(
        level=level_id,
        name=level_config["name"],
        description=level_config["description"],
        total_days=level_config["days"],
        days=days
    )


@router.get("/level/{level_id}/day/{day_number}", response_model=DayDetailResponse)
def get_day_detail(
    level_id: int,
    day_number: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get details for a specific day"""
    if level_id not in GRAPHOTHERAPY_LEVELS:
        raise HTTPException(status_code=404, detail="Level not found")
    
    level_config = GRAPHOTHERAPY_LEVELS[level_id]
    if day_number < 1 or day_number > level_config["days"]:
        raise HTTPException(status_code=404, detail="Day not found")
    
    progress = get_or_create_progress(db, current_user.id)
    today = date.today()
    
    # Check if day is unlocked
    # Day 1 is always unlocked
    # Other days are unlocked only if previous day was completed on a PREVIOUS calendar date
    is_unlocked = day_number == 1
    prev_completion = None
    if day_number > 1:
        prev_completion = db.query(GraphotherapyDayCompletion).filter(
            GraphotherapyDayCompletion.progress_id == progress.id,
            GraphotherapyDayCompletion.level == level_id,
            GraphotherapyDayCompletion.day_number == day_number - 1
        ).first()
        # Use time-based unlock check
        is_unlocked = is_day_unlocked_by_completion(prev_completion, today)
    
    # Also check if level is unlocked
    if level_id > 1:
        prev_level_config = GRAPHOTHERAPY_LEVELS[level_id - 1]
        prev_level_completions = db.query(GraphotherapyDayCompletion).filter(
            GraphotherapyDayCompletion.progress_id == progress.id,
            GraphotherapyDayCompletion.level == level_id - 1
        ).count()
        if prev_level_completions < prev_level_config["days"]:
            is_unlocked = False
    
    # Get completion info
    completion = db.query(GraphotherapyDayCompletion).filter(
        GraphotherapyDayCompletion.progress_id == progress.id,
        GraphotherapyDayCompletion.level == level_id,
        GraphotherapyDayCompletion.day_number == day_number
    ).first()
    
    # Can complete today if unlocked and not already completed
    can_complete = is_unlocked and completion is None
    
    return DayDetailResponse(
        level=level_id,
        day_number=day_number,
        is_unlocked=is_unlocked,
        is_completed=completion is not None,
        completed_at=completion.completed_at if completion else None,
        upload_url=completion.upload_url if completion else None,
        can_complete_today=can_complete
    )


@router.post("/level/{level_id}/day/{day_number}/complete", response_model=DayCompleteResponse)
async def complete_day(
    level_id: int,
    day_number: int,
    file: UploadFile = File(...),
    started_at: str = Form(None),
    duration_seconds: int = Form(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Complete a day by uploading practice image"""
    if level_id not in GRAPHOTHERAPY_LEVELS:
        raise HTTPException(status_code=404, detail="Level not found")
    
    level_config = GRAPHOTHERAPY_LEVELS[level_id]
    if day_number < 1 or day_number > level_config["days"]:
        raise HTTPException(status_code=404, detail="Day not found")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    progress = get_or_create_progress(db, current_user.id)
    
    # Check if already completed
    existing = db.query(GraphotherapyDayCompletion).filter(
        GraphotherapyDayCompletion.progress_id == progress.id,
        GraphotherapyDayCompletion.level == level_id,
        GraphotherapyDayCompletion.day_number == day_number
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Day already completed")
    
    # Check if day is unlocked
    if day_number > 1:
        prev_completion = db.query(GraphotherapyDayCompletion).filter(
            GraphotherapyDayCompletion.progress_id == progress.id,
            GraphotherapyDayCompletion.level == level_id,
            GraphotherapyDayCompletion.day_number == day_number - 1
        ).first()
        if not prev_completion:
            raise HTTPException(status_code=403, detail="Complete previous day first")
    
    # Check if level is unlocked
    if level_id > 1:
        prev_level_config = GRAPHOTHERAPY_LEVELS[level_id - 1]
        prev_level_completions = db.query(GraphotherapyDayCompletion).filter(
            GraphotherapyDayCompletion.progress_id == progress.id,
            GraphotherapyDayCompletion.level == level_id - 1
        ).count()
        if prev_level_completions < prev_level_config["days"]:
            raise HTTPException(status_code=403, detail="Complete previous level first")
    
    # Save uploaded file
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"{current_user.id}_{level_id}_{day_number}_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Create upload URL (relative path for serving)
    upload_url = f"/uploads/graphotherapy/{unique_filename}"
    
    # --- V2 Logic: Create GraphoSubmission & Verify ---
    book = db.query(GraphoBook).filter(GraphoBook.level == level_id).first()
    
    started_at_dt = None
    if started_at:
        try:
            started_at_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass

    submission = GraphoSubmission(
        user_id=current_user.id,
        book_id=book.id if book else None,
        day=day_number,
        image_url=upload_url,
        started_at=started_at_dt,
        duration_seconds=duration_seconds,
        status="pending"
    )
    db.add(submission)
    # --------------------------------------------------

    # Create completion record
    completion = GraphotherapyDayCompletion(
        progress_id=progress.id,
        level=level_id,
        day_number=day_number,
        upload_url=upload_url,
        upload_filename=file.filename
    )
    db.add(completion)
    
    # Update streak
    today = date.today()
    if progress.last_practice_date:
        last_practice = progress.last_practice_date.date()
        if last_practice == today - timedelta(days=1):
            progress.total_streak += 1
        elif last_practice != today:
            progress.total_streak = 1
    else:
        progress.total_streak = 1
    
    progress.last_practice_date = datetime.now()
    
    # Check if level is completed
    level_completions = db.query(GraphotherapyDayCompletion).filter(
        GraphotherapyDayCompletion.progress_id == progress.id,
        GraphotherapyDayCompletion.level == level_id
    ).count() + 1  # +1 for current completion
    
    level_completed = level_completions >= level_config["days"]
    next_level_unlocked = level_completed and level_id < 4
    
    # Update current level and day
    if level_completed and level_id < 4:
        # GRANDFATHER CLAUSE: Existing users (before Jan 15, 2026) get auto-unlock.
        # New users must pay for priced levels.
        cutoff_date = datetime(2026, 1, 15)
        is_legacy = current_user.created_at and current_user.created_at < cutoff_date
        
        next_level_price = GRAPHOTHERAPY_LEVELS[level_id + 1]["price"]
        
        # Auto-advance if: Legacy User OR Next Level is Free
        if is_legacy or next_level_price == 0:
            progress.current_level = level_id + 1
            progress.current_day = 1
        else:
            # New User + Paid Level = Paywall (Do not advance level)
            pass
            
    elif not level_completed:
        progress.current_day = day_number + 1
    
    db.commit()
    
    return DayCompleteResponse(
        success=True,
        message=f"Day {day_number} completed successfully!",
        upload_url=upload_url,
        new_streak=progress.total_streak,
        level_completed=level_completed,
        next_level_unlocked=next_level_unlocked
    )


    return {
        "current_streak": calculate_streak(progress),
        "total_streak": progress.total_streak,
        "last_practice_date": progress.last_practice_date
    }


# --- V2 Admin Endpoints ---

@router.post("/admin/books/upload", response_model=GraphoBookResponse)
async def upload_reference_book(
    title: str = Form(...),
    level: int = Form(...),
    total_days: int = Form(30),
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """
    Admin: Upload a PDF reference book for Graphotherapy.
    This stores the PDF and creates a GraphoBook record.
    """
    if not file.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Directory for reference books
    BOOKS_DIR = "uploads/graphotherapy/books"
    os.makedirs(BOOKS_DIR, exist_ok=True)

    # Save File
    file_ext = ".pdf"
    unique_filename = f"level_{level}_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(BOOKS_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Relative URL
    pdf_url = f"/uploads/graphotherapy/books/{unique_filename}"
    
    # Create DB Record
    book = GraphoBook(
        title=title,
        level=level,
        total_days=total_days,
        pdf_url=pdf_url,
        is_published=False 
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    
    return book

@router.get("/admin/books", response_model=List[GraphoBookResponse])
def get_all_books(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """Admin: List all reference books"""
    books = db.query(GraphoBook).offset(skip).limit(limit).all()
    return books

@router.get("/admin/submissions", response_model=List[GraphoSubmissionResponse])
def get_all_submissions(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """Admin: List student submissions"""
    query = db.query(GraphoSubmission)
    if status:
        query = query.filter(GraphoSubmission.status == status)
    
    submissions = query.order_by(GraphoSubmission.completed_at.desc()).offset(skip).limit(limit).all()
    return submissions


@router.post("/admin/submissions/{submission_id}/analyze", response_model=GraphoSubmissionResponse)
def analyze_submission(
    submission_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """
    Admin: Trigger AI Analysis for a submission.
    Generates a personality report based on the handwriting.
    """
    submission = db.query(GraphoSubmission).filter(GraphoSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # --- Real AI Analysis Logic ---
    from app.services.gemini_service import gemini_service
    import os
    import json
    
    # 1. Resolve File Path
    # image_url is like "/uploads/graphotherapy/filename.jpg" -> "uploads/graphotherapy/filename.jpg"
    relative_path = submission.image_url.lstrip("/")
    # Ensure it works cross-platform or with how app is run (cwd is usually root)
    image_path = os.path.abspath(relative_path)
    
    if not os.path.exists(image_path):
        # Fallback to verify if it exists in UPLOAD_DIR directly
        filename = os.path.basename(submission.image_url)
        params_path = os.path.join("uploads", "graphotherapy", filename)
        if os.path.exists(params_path):
            image_path = os.path.abspath(params_path)
        else:
             raise HTTPException(status_code=404, detail=f"Submission image file not found at {image_path}")

    # 2. Define Prompt
    ANALYSIS_PROMPT = """
    You are an expert Graphotherapist and Handwriting Analyst. 
    Analyze the requested handwriting sample image from a student's daily practice. 
    Provide a structured psychological analysis focusing on progress and traits:

    1. Emotional Stability (Baseline, Slant Consistency)
    2. Willpower & Determination (t-bars crossing strength)
    3. Self-Image & Ego (Capital letters, signature size)
    4. Focus & Concentration (Dotting of i's)
    5. Success/Money Blocks (Lower loops of g, y, j)

    Return the response in strict JSON format:
    {
        "overall_score": 0-100 (integer),
        "traits": [
            {"trait": "Trait Name", "score": 0-100, "observation": "detailed observation"}
        ],
        "metrics": [
             {"name": "Slant", "baseline_value": "Variable", "current_value": "Right/Vertical", "status": "Improved/Same", "change_percentage": 10},
             {"name": "Pressure", "baseline_value": "Heavy/Light", "current_value": "Balanced", "status": "Improved", "change_percentage": 5}
        ],
        "areas_of_concern": [
            {"stroke": "Claw/Retrace/etc", "meaning": "meaning", "fix": "suggested fix"}
        ],
        "summary": "2-3 sentences summary of progress and current state.",
        "transformation_score": 0-100 (integer representing overall improvement vs baseline if evident, else generic quality score)
    }
    """

    try:
        # 3. Call Gemini
        response_text = gemini_service.analyze_image(
            image_path=image_path,
            prompt=ANALYSIS_PROMPT,
            temperature=0.2
        )
        
        # 4. Parse JSON
        cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
        analysis_result = json.loads(cleaned_response)
        
        # Ensure timestamp
        analysis_result["generated_at"] = datetime.utcnow().isoformat()
        
    except Exception as e:
        print(f"AI Analysis Failed: {e}")
        # Fallback to avoid crashing the admin flow completely, but indicate error
        analysis_result = {
            "overall_score": 0,
            "traits": [],
            "summary": f"AI Analysis failed: {str(e)}",
            "error": str(e),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    # Generate PDF Report
    from app.utils.report_generator import report_generator
    # Note: user_name should ideally come from user relationship, here using logic stub
    user_name = f"Student #{submission.user_id}" 
    pdf_url = report_generator.generate_report(submission.id, user_name, analysis_result)
    
    # Update Submission
    submission.analysis_result = analysis_result
    submission.status = "analyzed"
    submission.verification_score = analysis_result["overall_score"]
    # We might want to store pdf_url in analysis_result or a new column
    analysis_result['pdf_url'] = pdf_url
    submission.analysis_result = analysis_result # Update with PDF URL
    
    db.commit()
    db.refresh(submission)
    
    return submission


# --- Phase 4: Transformation & Prediction Endpoints ---

from app.schemas.graphotherapy import (
    TransformationComparisonRequest,
    TransformationComparisonResponse,
    ComparisonMetric,
    NextStepRecommendation,
    GrowthDomain
)

@router.post("/transform/compare", response_model=TransformationComparisonResponse)
def compare_transformation(
    request: TransformationComparisonRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Compare Day 1 (Baseline) vs Day 21 (Current) handwriting.
    Generates AI-driven transformation report.
    """
    user_id = request.user_id if request.user_id and current_user.is_superuser else current_user.id
    progress = get_or_create_progress(db, user_id)

    # Helper to clean logic
    def get_image_for_day(day_num: int):
        # Check Day Completion
        completion = db.query(GraphotherapyDayCompletion).filter(
            GraphotherapyDayCompletion.progress_id == progress.id,
            GraphotherapyDayCompletion.day_number == day_num
        ).first()
        if completion and completion.upload_url:
            return completion.upload_url
        
        # Check Submission (legacy/admin flow)
        submission = db.query(GraphoSubmission).filter(
            GraphoSubmission.user_id == user_id,
            GraphoSubmission.day == day_num
        ).first()
        if submission and submission.image_url:
            return submission.image_url
            
        return None

    baseline_url = get_image_for_day(request.baseline_day)
    current_url = get_image_for_day(request.current_day)

    # --- Real AI Comparison Logic ---
    from app.services.gemini_service import gemini_service
    import json
    
    # Define Prompt
    COMPARISON_PROMPT = """
    Act as a Master Graphologist. Compare these two handwriting samples.
    Image 1 is the 'Baseline' (Day 1). Image 2 is the 'Current' (Day 21) progress.

    Analyze the neurological transformation based on:
    1. Slant Consistency (Is it more stable?)
    2. Letter Connectedness (Fluidity of thought)
    3. Baseline Adherence (Emotional stability)
    4. Pressure (Energy levels)

    Return ONLY a valid JSON object with this structure:
    {
        "transformation_score": <integer 0-100>,
        "qualitative_feedback": "<string, a short encouraging paragraph about the specific improvements>",
        "metrics": [
            {"name": "Slant Stability", "baseline_value": "Variable", "current_value": "Stable", "status": "Improved/Stable/Needs Work", "change_percentage": 20},
            {"name": "Letter Connectedness", "baseline_value": "Disconnected", "current_value": "Fluid", "status": "Improved/Stable/Needs Work", "change_percentage": 15},
            {"name": "Baseline Adherence", "baseline_value": "Wavy", "current_value": "Straight", "status": "Improved/Stable/Needs Work", "change_percentage": 10},
            {"name": "Pressure", "baseline_value": "Heavy", "current_value": "Balanced", "status": "Improved/Stable/Needs Work", "change_percentage": 5}
        ]
    }
    """

    try:
        # Resolve paths
        def resolve_path(url):
            if not url: return None
            rel = url.lstrip("/")
            # Check standard upload dir
            if os.path.exists(rel): return os.path.abspath(rel)
            # Check if it is a full path or absolute
            if os.path.exists(url): return url
            # Fallback
            return None

        path1 = resolve_path(baseline_url)
        path2 = resolve_path(current_url)

        if not path1 or not path2:
             # Fallback if images missing (e.g. legacy data)
             analysis_result = {
                 "transformation_score": 0,
                 "qualitative_feedback": "Images for comparison could not be located.",
                 "metrics": []
             }
        else:
             response_text = gemini_service.compare_images(path1, path2, COMPARISON_PROMPT)
             clean_json = response_text.replace("```json", "").replace("```", "").strip()
             analysis_result = json.loads(clean_json)

    except Exception as e:
        print(f"Comparison Failed: {e}")
        analysis_result = {
             "transformation_score": 0,
             "qualitative_feedback": f"AI Comparison failed: {str(e)}",
             "metrics": []
        }
    
    metrics = [
        ComparisonMetric(
            name=m["name"], 
            baseline_value=str(m["baseline_value"]), 
            current_value=str(m["current_value"]),
            change_percentage=m.get("change_percentage", 0),
            status=m["status"]
        ) for m in analysis_result.get("metrics", [])
    ]

    return TransformationComparisonResponse(
        baseline_image_url=baseline_url, # Corrected to use local variable
        current_image_url=current_url,    # Corrected to use local variable
        transformation_score=analysis_result.get("transformation_score", 0),
        qualitative_feedback=analysis_result.get("qualitative_feedback", "Analysis unavailable."),
        metrics=metrics,
        generated_at=datetime.utcnow() # Re-added generated_at
    )


@router.get("/predict/next-steps", response_model=NextStepRecommendation)
def predict_next_steps(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Predict next growth domain based on user progress and performance.
    """
    progress = get_or_create_progress(db, current_user.id)
    
    # Logic Rules
    recommendation = None
    alternatives = []
    context = ""

    if progress.current_level == 1 and progress.current_day >= 21:
        # Completed Foundation
        recommendation = GrowthDomain(
            id="level_2",
            title="Intermediate Level: Letter Formations",
            description="Deep dive into 't' crossings, 'i' dots and loops.",
            icon="feather",
            is_locked=False,
            unlock_criteria="Unlocked"
        )
        context = "You have established a solid foundation. Now let's refine individual traits."
    elif progress.total_streak > 15:
         recommendation = GrowthDomain(
            id="speed_drill",
            title="Speed & Flow Challenge",
            description="Maintain quality while increasing writing speed.",
            icon="timer",
            is_locked=False,
            unlock_criteria="Unlocked"
        )
         context = f"Your {progress.total_streak}-day streak shows great discipline!"
    else:
        # Default
        recommendation = GrowthDomain(
            id="consistency_mastery",
            title="Consistency Builder",
            description="Focus on slant regularity for 7 more days.",
            icon="target",
            is_locked=False,
            unlock_criteria="Unlocked"
        )
        context = "Building consistency is your key lever right now."

    # Alternatives
    alternatives.append(GrowthDomain(
        id="signature_analysis",
        title="Signature Analysis",
        description="What your signature says about your public image.",
        icon="pen-tool",
        is_locked=True,
        unlock_criteria="Requires Level 2 Completion"
    ))

    return NextStepRecommendation(
        primary_recommendation=recommendation,
        alternatives=alternatives,
        user_context=context
    )


# --- Phase 5: Community Endpoints ---

from app.schemas.graphotherapy import LeaderboardEntry, ShareResponse, PurchaseRequest, PurchaseResponse, GRAPHOTHERAPY_LEVELS
from fastapi import HTTPException
import uuid

@router.get("/community/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get top users by streak.
    """
    # Query top streaks
    top_progress = db.query(GraphotherapyProgress).order_by(
        GraphotherapyProgress.total_streak.desc()
    ).limit(limit).all()
    
    leaderboard = []
    for i, p in enumerate(top_progress):
        user = db.query(User).filter(User.id == p.user_id).first()
        user_name = user.full_name if user else f"User {p.user_id}"
        # Privacy: Mask name if not current user (optional, for now showing full name)
        
        leaderboard.append(LeaderboardEntry(
            rank=i + 1,
            user_name=user_name,
            streak=p.total_streak,
            avatar_url=None, # Add avatar to User model later
            is_current_user=(p.user_id == current_user.id)
        ))
        
    return leaderboard

@router.post("/share/transformation", response_model=ShareResponse)
def share_transformation(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Generate a public share link for the user's transformation.
    """
    # In a real app, generate a unique token and store a 'SharedReport' record.
    # For now, return a constructed URL.
    share_id = uuid.uuid4().hex[:8]
    share_url = f"https://eduecosystem.com/share/grapho/{share_id}"
    
    return ShareResponse(
        share_url=share_url,
        message="Transformation report link generated successfully!"
    )

@router.post("/purchase", response_model=PurchaseResponse)
def purchase_level(
    request: PurchaseRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Purchase a level, bundle, or gamification item.
    Logic:
    - Streak Freeze: Flat 500 Coins.
    - Levels: 10 Coins = 1 Rs discount. Max 1000 Rs discount.
    """
    transaction_id = f"txn_{uuid.uuid4().hex[:8]}"
    
    # --- STREAK FREEZE ---
    if request.item_type == "streak_freeze":
        cost = 500
        if current_user.coins < cost:
             raise HTTPException(status_code=400, detail="Insufficient coins for Streak Freeze")
        
        current_user.coins -= cost
        # Logic to 'activate' freeze would go here (e.g. set a flag on progress)
        # For prototype, we verify coin deduction.
        db.commit()
        
        return PurchaseResponse(
            success=True,
            transaction_id=transaction_id,
            final_price=0,
            coins_deducted=cost,
            message="Streak Freeze Activated! You are protected for 24 hours.",
            new_coin_balance=current_user.coins
        )

    # --- LEVEL UNLOCK ---
    base_price = 0
    discount_msg = ""
    
    # 1. Determine Base Price
    if request.is_bundle:
        # Calculate price of all remaining paid levels (2, 3, 4)
        base_price = sum(l["price"] for k, l in GRAPHOTHERAPY_LEVELS.items() if l["price"] > 0)
        discount_msg = "Bundle Discount (Lvl 2+3+4) Applied"
    else:
        req_level = GRAPHOTHERAPY_LEVELS.get(request.level_id)
        if not req_level:
            raise HTTPException(status_code=404, detail="Level not found")
        base_price = req_level["price"]
        discount_msg = "Standard Purchase"

    final_price = base_price
    coins_deducted = 0

    # 2. Apply Bundle Discount (Flat 5000 off)
    if request.is_bundle:
        final_price -= 5000
        if final_price < 0: final_price = 0

    # 3. Apply Coin Discount
    if request.use_coins and current_user.coins > 0:
        # Logic: 10 Coins = 1 Rs
        max_discount_rupees = 1000 
        max_discount_coins = max_discount_rupees * 10
        
        potential_discount_coins = min(current_user.coins, max_discount_coins)
        discount_amount = potential_discount_coins / 10
        
        if discount_amount > final_price:
            discount_amount = final_price
            potential_discount_coins = discount_amount * 10
            
        final_price -= discount_amount
        coins_deducted = int(potential_discount_coins)
        
        current_user.coins -= coins_deducted
        discount_msg += f" + Coin Discount ({coins_deducted} coins)"

    # 4. Process "Payment" (Mock)
    
    # 5. Unlock Logic
    progress = db.query(GraphotherapyProgress).filter(GraphotherapyProgress.user_id == current_user.id).first()
    if progress:
        if request.is_bundle:
            progress.current_level = 4 # Unlock all
            progress.current_day = 1
        elif request.level_id > progress.current_level:
             # Unlock specific level
             progress.current_level = request.level_id
             progress.current_day = 1 
    
    db.commit()

    return PurchaseResponse(
        success=True,
        transaction_id=transaction_id,
        final_price=int(final_price),
        coins_deducted=coins_deducted,
        message=f"Purchase successful! ({discount_msg})",
        new_coin_balance=current_user.coins
    )
