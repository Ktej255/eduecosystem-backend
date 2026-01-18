"""
Retention System API Endpoints
FSRS-based knowledge tracking and review scheduling.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from app.api import deps
from app.db.session import get_db
from app.models.user import User


router = APIRouter()


# ============ SCHEMAS ============

class EncodingSubmission(BaseModel):
    """Submit Feynman summary after watching video"""
    topic_id: int
    topic_type: str = "video"  # video, lesson, meditation
    topic_name: Optional[str] = None
    user_summary: str  # Text summary from student
    audio_transcript: Optional[str] = None


class EncodingResponse(BaseModel):
    topic_id: int
    comprehension_score: float
    status: str  # learned, weak_encoding
    feedback: Optional[str] = None
    next_review_date: Optional[datetime] = None


class MidnightTestSubmission(BaseModel):
    """Submit midnight test answers"""
    topic_id: int
    user_answer: str
    question_id: Optional[int] = None


class MidnightTestResponse(BaseModel):
    topic_id: int
    grade: int  # 1-4 FSRS grade
    score: float
    new_stability: float
    next_review_date: datetime
    feedback: Optional[str] = None


class TopicRetentionStatus(BaseModel):
    topic_id: int
    topic_name: str
    stability: float
    retrievability: float
    status: str  # mastered, stable, review_soon, critical, forgotten
    color: str  # green, yellow, red
    days_until_review: int
    next_review_date: Optional[datetime]
    last_reviewed: Optional[datetime]


class ExperienceSubmission(BaseModel):
    title: str
    reflections: str
    gunas: Dict[str, int]  # sattva, rajas, tamas


class ExperienceResponse(BaseModel):
    success: bool
    guru_insight: str
    spiritual_state: str  # e.g., "Sattvic flowing into Rajas"
    consciousness_score: int


class DashboardData(BaseModel):
    topics: List[TopicRetentionStatus]
    due_today: int
    critical_count: int
    average_retention: float


class CycleSessionSubmission(BaseModel):
    """Data from a completed 25-minute cycle"""
    topic_id: int
    cycle_type: str = "beginner_25m"
    duration_minutes: int = 25
    recall_score: float = 0.0
    mcq_score: float = 0.0
    verbal_transcript: Optional[str] = None
    week_id: Optional[int] = None
    day_id: Optional[int] = None


# ============ TREE SCHEMAS ============

class TreeLeafSchema(BaseModel):
    id: str
    topicId: str
    topicName: str
    subjectId: str
    retentionScore: float
    lastReviewed: Optional[datetime]
    status: str

class TreeBranchSchema(BaseModel):
    id: str
    subjectId: str
    subjectName: str
    leaves: List[TreeLeafSchema]


# ============ ENDPOINTS ============

@router.post("/submit-encoding", response_model=EncodingResponse)
async def submit_encoding(
    submission: EncodingSubmission,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Submit Feynman explanation after watching 25-min video.
    AI analyzes comprehension and creates initial retention record.
    """
    from app.models.retention import UserTopicLog, RetentionReview
    from app.utils.fsrs import calculate_initial_stability, convert_score_to_grade, calculate_next_interval
    
    # Check if topic already exists for this user
    existing = db.query(UserTopicLog).filter(
        UserTopicLog.user_id == current_user.id,
        UserTopicLog.topic_id == submission.topic_id,
        UserTopicLog.topic_type == submission.topic_type
    ).first()
    
    # Use Gemini Flash AI to analyze comprehension
    from app.services.gemini_service import gemini_service
    
    # Define key concepts (in production, these would come from the video metadata)
    key_concepts = [
        "Main topic understanding",
        "Key terminology usage", 
        "Logical explanation flow",
        "Practical applications mentioned",
        "Core concepts covered"
    ]
    
    # AI Analysis
    ai_result = gemini_service.analyze_comprehension(
        student_summary=submission.user_summary,
        key_concepts=key_concepts,
        user=current_user
    )
    
    comprehension_score = ai_result["score"]
    feedback = ai_result["feedback"]
    
    # Convert to grade and calculate stability
    grade = convert_score_to_grade(comprehension_score)
    initial_stability = calculate_initial_stability(comprehension_score)
    next_interval = calculate_next_interval(initial_stability)
    
    now = datetime.now(timezone.utc)
    next_review = now + timedelta(days=next_interval)
    
    if existing:
        # Update existing record
        existing.initial_encoding_score = comprehension_score
        existing.stability = initial_stability
        existing.retrievability = 1.0
        existing.last_review_date = now
        existing.next_due_date = next_review
        existing.status = "learned" if comprehension_score >= 0.6 else "weak_encoding"
        topic_log = existing
    else:
        # Create new record
        topic_log = UserTopicLog(
            user_id=current_user.id,
            topic_id=submission.topic_id,
            topic_type=submission.topic_type,
            topic_name=submission.topic_name,
            initial_encoding_score=comprehension_score,
            stability=initial_stability,
            difficulty=5.0,  # Default difficulty
            retrievability=1.0,
            learned_at=now,
            last_review_date=now,
            next_due_date=next_review,
            status="learned" if comprehension_score >= 0.6 else "weak_encoding"
        )
        db.add(topic_log)
    
    # Log the review
    review = RetentionReview(
        topic_log_id=topic_log.id if existing else None,  # Will be set after flush
        user_id=current_user.id,
        review_type="feynman_summary",
        score=comprehension_score,
        stability_before=existing.stability if existing else 0,
        stability_after=initial_stability,
        retrievability_at_review=1.0,
        user_input=submission.user_summary
    )
    
    db.commit()
    
    # Update review with topic_log_id if new
    if not existing:
        review.topic_log_id = topic_log.id
        db.add(review)
        db.commit()
    
    return EncodingResponse(
        topic_id=submission.topic_id,
        comprehension_score=comprehension_score,
        status=topic_log.status,
        feedback=feedback,  # Use AI-generated feedback
        next_review_date=next_review
    )


@router.post("/process-midnight-test", response_model=MidnightTestResponse)
async def process_midnight_test(
    submission: MidnightTestSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Process midnight test results and update FSRS stability.
    """
    from app.models.retention import UserTopicLog, RetentionReview
    from app.utils.fsrs import (
        update_stability_on_grade,
        convert_score_to_grade,
        calculate_next_interval,
        calculate_retrievability
    )
    
    # Find topic log
    topic_log = db.query(UserTopicLog).filter(
        UserTopicLog.user_id == current_user.id,
        UserTopicLog.topic_id == submission.topic_id
    ).first()
    
    if not topic_log:
        raise HTTPException(status_code=404, detail="Topic not found in your learning log")
    
    now = datetime.now(timezone.utc)
    
    # Calculate days elapsed since last review
    days_elapsed = 0
    if topic_log.last_review_date:
        days_elapsed = (now - topic_log.last_review_date).total_seconds() / 86400
    
    # Real AI analysis of answer using Gemini
    from app.services.gemini_service import gemini_service
    
    # Identify topic info for better prompting
    from app.models.lesson import Lesson
    lesson = db.query(Lesson).filter(Lesson.id == submission.topic_id).first()
    topic_name = lesson.title if lesson else "this topic"
    
    # Analyze comprehension via AI
    ai_result = gemini_service.analyze_comprehension(
        student_summary=submission.user_answer,
        key_concepts=[topic_name, "core principles", "practical application"],
        user=current_user
    )
    
    score = ai_result.get("score", 0.5)
    grade = ai_result.get("grade", convert_score_to_grade(score))
    
    # Calculate current retrievability before update
    current_r = calculate_retrievability(topic_log.stability, days_elapsed)
    
    # Update stability based on grade
    old_stability = topic_log.stability
    new_stability, new_difficulty = update_stability_on_grade(
        topic_log.stability,
        topic_log.difficulty,
        grade,
        days_elapsed
    )
    
    # Calculate next review date
    next_interval = calculate_next_interval(new_stability)
    next_review = now + timedelta(days=next_interval)
    
    # Update topic log
    topic_log.stability = new_stability
    topic_log.difficulty = new_difficulty
    topic_log.retrievability = 1.0  # Reset after review
    topic_log.last_recall_grade = grade
    topic_log.last_review_date = now
    topic_log.next_due_date = next_review
    topic_log.total_reviews += 1
    if grade >= 3:
        topic_log.successful_recalls += 1
    
    # Update status
    if new_stability >= 30 and topic_log.successful_recalls >= 3:
        topic_log.status = "mastered"
    elif grade == 1:
        topic_log.status = "forgotten"
    else:
        topic_log.status = "reviewing"
    
    # Log review
    review = RetentionReview(
        topic_log_id=topic_log.id,
        user_id=current_user.id,
        review_type="midnight_test",
        grade=grade,
        score=score,
        stability_before=old_stability,
        stability_after=new_stability,
        retrievability_at_review=current_r,
        user_input=submission.user_answer
    )
    db.add(review)
    db.commit()
    
    return MidnightTestResponse(
        topic_id=submission.topic_id,
        grade=grade,
        score=score,
        new_stability=new_stability,
        next_review_date=next_review,
        feedback=get_grade_feedback(grade)
    )


@router.get("/dashboard", response_model=DashboardData)
async def get_retention_dashboard(
    days: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get 10-day retention dashboard with heatmap data.
    """
    from app.models.retention import UserTopicLog
    from app.utils.fsrs import calculate_retrievability, get_retention_status, get_color_for_retention, calculate_next_interval
    
    now = datetime.now(timezone.utc)
    
    # Get all topics for this user
    topics = db.query(UserTopicLog).filter(
        UserTopicLog.user_id == current_user.id,
        UserTopicLog.is_active == True
    ).all()
    
    topic_statuses = []
    due_today = 0
    critical_count = 0
    total_retention = 0
    
    for topic in topics:
        # Calculate current retrievability
        days_elapsed = 0
        if topic.last_review_date:
            days_elapsed = (now - topic.last_review_date).total_seconds() / 86400
        
        current_r = calculate_retrievability(topic.stability, days_elapsed)
        status = get_retention_status(current_r)
        color = get_color_for_retention(current_r)
        
        days_until = 0
        if topic.next_due_date:
            days_until = max(0, (topic.next_due_date - now).days)
        
        if days_until <= 0:
            due_today += 1
        if status == "critical" or status == "forgotten":
            critical_count += 1
        
        total_retention += current_r
        
        topic_statuses.append(TopicRetentionStatus(
            topic_id=topic.topic_id,
            topic_name=topic.topic_name or f"Topic {topic.topic_id}",
            stability=topic.stability,
            retrievability=current_r,
            status=status,
            color=color,
            days_until_review=days_until,
            next_review_date=topic.next_due_date,
            last_reviewed=topic.last_review_date
        ))
    
    avg_retention = total_retention / len(topics) if topics else 0
    
    return DashboardData(
        topics=topic_statuses,
        due_today=due_today,
        critical_count=critical_count,
        average_retention=avg_retention
    )


@router.get("/due-topics")
async def get_due_topics(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get topics that are due for review today."""
    from app.models.retention import UserTopicLog
    
    now = datetime.now(timezone.utc)
    
    due_topics = db.query(UserTopicLog).filter(
        UserTopicLog.user_id == current_user.id,
        UserTopicLog.next_due_date <= now,
        UserTopicLog.is_active == True
    ).all()
    
    return {"due_topics": [t.topic_id for t in due_topics], "count": len(due_topics)}


@router.get("/decay-curve/{topic_id}")
async def get_decay_curve(
    topic_id: int,
    days: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get decay curve data points for visualization."""
    from app.models.retention import UserTopicLog
    from app.utils.fsrs import generate_decay_curve_points
    
    topic = db.query(UserTopicLog).filter(
        UserTopicLog.user_id == current_user.id,
        UserTopicLog.topic_id == topic_id
    ).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    points = generate_decay_curve_points(topic.stability, days)
    
    return {
        "topic_id": topic_id,
        "topic_name": topic.topic_name,
        "stability": topic.stability,
        "curve_points": points
    }


@router.get("/tree", response_model=List[TreeBranchSchema])
async def get_knowledge_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get hierarchical data for 3D Knowledge Tree.
    Joins UserTopicLog -> Lesson -> Module -> Course to group topics by Subject (Course).
    """
    from sqlalchemy.orm import joinedload
    
    # Efficiently fetch logs with related hierarchy info
    logs = (
        db.query(UserTopicLog)
        .options(joinedload(UserTopicLog.user)) # Just in case, though not needed here
        .filter(UserTopicLog.user_id == current_user.id)
        .all()
    )
    
    branches = {}  # course_id -> { info, leaves }
    now = datetime.now(timezone.utc)
    
    for log in logs:
        # Resolve Hierarchy using a single join-based helper or manual lookup
        # Since UserTopicLog.topic_id is a Lesson ID (usually)
        from app.models.lesson import Lesson
        from app.models.module import Module
        from app.models.course import Course
        
        # We still need course info. A single join query would be better:
        data = (
            db.query(Lesson, Module, Course)
            .join(Module, Lesson.module_id == Module.id)
            .join(Course, Module.course_id == Course.id)
            .filter(Lesson.id == log.topic_id)
            .first()
        )
        
        if not data:
            continue
            
        lesson, module, course = data
            
        # Determine Status
        days_elapsed = 0
        if log.last_review_date:
            days_elapsed = (now - log.last_review_date).total_seconds() / 86400
            
        # Use existing status if it makes sense, or retrievability
        current_r = calculate_retrievability(log.stability, days_elapsed)
        retention_score = current_r * 100
        
        # Garden-themed Status Mapping
        if log.status == "mastered" or retention_score > 85:
            status = "blooming"
        elif log.status == "forgotten" or retention_score < 40:
            status = "withered"
        else:
            status = "healthy"
            
        # Add to Branch
        course_id = str(course.id)
        if course_id not in branches:
            branches[course_id] = {
                "id": f"branch-{course.id}",
                "subjectId": course_id,
                "subjectName": course.title,
                "leaves": []
            }
            
        branches[course_id]["leaves"].append(TreeLeafSchema(
            id=f"leaf-{log.id}",
            topicId=str(log.topic_id),
            topicName=lesson.title,
            subjectId=course_id,
            retentionScore=round(retention_score, 1),
            lastReviewed=log.last_review_date,
            status=status
        ))
        
    return list(branches.values())


# ============ EXPERIENCE ENDPOINT ============

@router.post("/experience", response_model=ExperienceResponse)
async def analyze_experience(
    submission: ExperienceSubmission,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Analyze partial spiritual experience reports.
    Uses Gemini to provide "Guru-like" insight based on gunas and reflection.
    """
    from app.services.gemini_service import gemini_service
    
    # Construct prompt for the "Guru" persona
    prompt = f"""
    Act as an enlightened Vedantic Master (Guru). 
    Student Reflection on {submission.title}:
    "{submission.reflections}"
    
    Current Guna State:
    - Sattva: {submission.gunas.get('sattva', 0)}%
    - Rajas: {submission.gunas.get('rajas', 0)}%
    - Tamas: {submission.gunas.get('tamas', 0)}%
    
    Provide a brief, profound insight (2-3 sentences max) to guide them deeper.
    Also, identify their primary spiritual state (e.g., "Peaceful Contemplation", "Restless Seeking").
    And assign a "Consciousness Alignment Score" (1-100) based on clarity.
    
    Return JSON: {{ "insight": "...", "state": "...", "score": 85 }}
    """
    
    try:
        response_text = gemini_service.generate_text(prompt, temperature=0.7, json_mode=True)
        import json
        # Extract JSON if wrapped (gemini_service helper does this but doing it safely here too)
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        return ExperienceResponse(
            success=True,
            guru_insight=data.get("insight", "Keep looking within."),
            spiritual_state=data.get("state", "Contemplation"),
            consciousness_score=data.get("score", 70)
        )
    except Exception as e:
        print(f"Experience Analysis Error: {e}")
        # Fallback if AI fails
        return ExperienceResponse(
            success=True,
            guru_insight="Your sincere reflection is itself the path. Continue your Sadhana.",
            spiritual_state="Introspection",
            consciousness_score=75
        )


# ============ CYCLE PERSISTENCE ============

@router.post("/cycle", response_model=Dict)
async def submit_cycle_session(
    submission: CycleSessionSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Save specific revision cycle data and update FSRS retention.
    """
    from app.models.retention import UserTopicLog, RevisionCycle, RetentionReview
    from app.utils.fsrs import calculate_initial_stability, calculate_next_interval, update_stability_on_grade
    
    # 1. Save detailed cycle record
    cycle = RevisionCycle(
        user_id=current_user.id,
        topic_id=submission.topic_id,
        cycle_type=submission.cycle_type,
        duration_minutes=submission.duration_minutes,
        recall_score=submission.recall_score,
        mcq_score=submission.mcq_score,
        total_score=(submission.recall_score + submission.mcq_score) / 2,
        verbal_transcript=submission.verbal_transcript
    )
    db.add(cycle)
    
    # 2. Update FSRS Logic (Memory Stability)
    
    # NEW: AI Scoring for Verbal Recall if transcript exists
    actual_recall_score = submission.recall_score
    if submission.verbal_transcript and len(submission.verbal_transcript.split()) > 5:
        from app.services.gemini_service import gemini_service
        # Identify topic name for context
        from app.models.lesson import Lesson
        lesson = db.query(Lesson).filter(Lesson.id == submission.topic_id).first()
        topic_name = lesson.title if lesson else f"Topic {submission.topic_id}"
        
        ai_result = gemini_service.analyze_comprehension(
            student_summary=submission.verbal_transcript,
            key_concepts=[topic_name, "concepts learned in session"],
            user=current_user
        )
        actual_recall_score = ai_result.get("score", 0.5) * 100
        cycle.recall_score = actual_recall_score
        cycle.total_score = (actual_recall_score + submission.mcq_score) / 2

    # Calculate a grade (1-4) based on the total score
    total_score_percent = cycle.total_score
    grade = 1
    if total_score_percent > 90: grade = 4
    elif total_score_percent > 75: grade = 3
    elif total_score_percent > 50: grade = 2
    
    # Find existing topic log
    topic_log = db.query(UserTopicLog).filter(
        UserTopicLog.user_id == current_user.id,
        UserTopicLog.topic_id == submission.topic_id
    ).first()
    
    now = datetime.now(timezone.utc)
    
    if topic_log:
        # Update existing Record using FSRS
        old_stability = topic_log.stability
        days_elapsed = 0
        if topic_log.last_review_date:
            days_elapsed = (now - topic_log.last_review_date).total_seconds() / 86400
            
        new_stability, new_difficulty = update_stability_on_grade(
            topic_log.stability,
            topic_log.difficulty,
            grade,
            days_elapsed
        )
        
        topic_log.stability = new_stability
        topic_log.difficulty = new_difficulty
        topic_log.last_recall_grade = grade
        topic_log.last_review_date = now
        topic_log.total_reviews += 1
        
        cycle.user_topic_log_id = topic_log.id
        
        # Log Review for Analytics
        review = RetentionReview(
            topic_log_id=topic_log.id,
            user_id=current_user.id,
            review_type="cycle_session",
            grade=grade,
            score=total_score_percent / 100,
            stability_before=old_stability,
            stability_after=new_stability,
            user_input=f"Cycle: {submission.cycle_type}"
        )
        db.add(review)
        
    else:
        # First time learning this topic
        initial_s = calculate_initial_stability(total_score_percent / 100)
        topic_log = UserTopicLog(
            user_id=current_user.id,
            topic_id=submission.topic_id,
            topic_type="video", # Default
            topic_name=f"Topic {submission.topic_id}",
            stability=initial_s,
            retrievability=1.0,
            status="learned",
            last_review_date=now,
            next_due_date=now + timedelta(days=calculate_next_interval(initial_s))
        )
        db.add(topic_log)
        db.flush() # Get ID
        cycle.user_topic_log_id = topic_log.id

    db.commit()
    return {"success": True, "cycle_id": cycle.id, "new_stability": topic_log.stability}


# ============ HELPERS ============

def get_grade_feedback(grade: int) -> str:
    """Get feedback message for FSRS grade."""
    feedback = {
        1: "Don't worry! Review the material again and try the test tomorrow.",
        2: "Good effort! You recalled most of it. A quick review will help.",
        3: "Great job! Your memory is solidifying. Keep it up!",
        4: "Excellent! Perfect recall. This topic is becoming mastered!"
    }
    return feedback.get(grade, "Review complete.")
