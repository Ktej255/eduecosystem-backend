"""
Retention System API Endpoints
FSRS-based knowledge tracking and review scheduling.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
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


class DashboardData(BaseModel):
    topics: List[TopicRetentionStatus]
    due_today: int
    critical_count: int
    average_retention: float


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
    
    # TODO: AI analysis of answer
    # Placeholder scoring
    answer_words = len(submission.user_answer.split())
    score = min(1.0, answer_words / 50)
    grade = convert_score_to_grade(score)
    
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
