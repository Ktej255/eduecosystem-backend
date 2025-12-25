"""
Engagement API Endpoints
Connect The Dots, Daily Wisdom, and engagement rewards.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
import random

from app.api import deps
from app.db.session import get_db
from app.models.user import User


router = APIRouter()


# ============ SCHEMAS ============

class ConnectionSubmission(BaseModel):
    current_topic_id: int
    previous_topic_id: int
    connection_text: str


class ConnectionResponse(BaseModel):
    success: bool
    coins_earned: int
    ai_feedback: Optional[str]
    quality_score: float


class DailyWisdom(BaseModel):
    id: int
    title: str
    content: str
    topic_related: Optional[str]
    date: str


# ============ DAILY WISDOM ============

WISDOM_LIBRARY = [
    {
        "title": "The Power of Breath",
        "content": "Your breath is the bridge between body and mind. 3 conscious breaths can reduce cortisol by 25%.",
        "topic": "Breath Awareness"
    },
    {
        "title": "Why Counting Matters",
        "content": "Counting creates a focal point. When the mind wanders, the count breaks - making awareness automatic.",
        "topic": "Counting Breath"
    },
    {
        "title": "Om Vibration Science",
        "content": "Om chanting at 7.83 Hz matches Earth's Schumann resonance. Your cells literally sync with the planet.",
        "topic": "Om Chanting"
    },
    {
        "title": "Relaxation Response",
        "content": "Dr. Herbert Benson discovered: 20 mins of relaxation = 4 hours of sleep for brain recovery.",
        "topic": "Relaxation"
    },
    {
        "title": "Memory & Meditation",
        "content": "8 weeks of daily meditation increases grey matter in the hippocampus by 3% - that's measurable memory improvement.",
        "topic": "General"
    },
    {
        "title": "The Forgetting Curve",
        "content": "Without review, you forget 70% in 24 hours. But space your reviews right, and retention becomes permanent.",
        "topic": "Retention"
    },
    {
        "title": "Connection is Retention",
        "content": "Linking new knowledge to existing memories creates 3x stronger neural pathways than isolated learning.",
        "topic": "Connect The Dots"
    },
    {
        "title": "Graphotherapy Science",
        "content": "Your handwriting reflects brain patterns. Changing your writing can literally rewire neural pathways.",
        "topic": "Graphotherapy"
    },
]


@router.get("/daily-wisdom", response_model=DailyWisdom)
async def get_daily_wisdom(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get today's wisdom nugget"""
    # Use date as seed for consistent daily wisdom
    today = datetime.now(timezone.utc).date()
    seed = int(today.strftime("%Y%m%d"))
    random.seed(seed)
    
    wisdom = random.choice(WISDOM_LIBRARY)
    
    return DailyWisdom(
        id=seed % 1000,
        title=wisdom["title"],
        content=wisdom["content"],
        topic_related=wisdom.get("topic"),
        date=str(today)
    )


# ============ CONNECT THE DOTS ============

@router.post("/submit-connection", response_model=ConnectionResponse)
async def submit_connection(
    submission: ConnectionSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Submit a concept connection for coins.
    AI analyzes quality and awards coins.
    """
    from app.models.coin_transaction import CoinTransaction, TransactionType
    from app.services.gemini_service import gemini_service
    
    # Basic quality check
    word_count = len(submission.connection_text.split())
    
    if word_count < 5:
        raise HTTPException(status_code=400, detail="Connection too short. Please write at least one sentence.")
    
    # AI quality analysis
    try:
        prompt = f"""Rate this concept connection on a scale of 0-1:
        
Connection: "{submission.connection_text}"

Consider:
- Does it show understanding of both concepts?
- Is it a meaningful connection or just surface-level?
- Would this help someone learn?

Respond with ONLY a number between 0 and 1."""

        response = gemini_service.generate_text(prompt, user=current_user, temperature=0.3, max_tokens=50)
        quality_score = float(response.strip())
        quality_score = max(0.0, min(1.0, quality_score))
    except:
        # Fallback: word-count based scoring
        quality_score = min(1.0, word_count / 30)
    
    # Calculate coins based on quality
    base_coins = 10
    quality_bonus = int(quality_score * 10)
    total_coins = base_coins + quality_bonus
    
    # Award coins
    current_user.coins += total_coins
    
    # Log transaction
    transaction = CoinTransaction(
        user_id=current_user.id,
        amount=total_coins,
        type=TransactionType.EARNED,
        reason="connect_the_dots",
        description=f"Connected topics: {submission.connection_text[:50]}...",
        reference_type="connection",
        reference_id=submission.current_topic_id,
        balance_after=current_user.coins
    )
    db.add(transaction)
    db.commit()
    
    # Generate feedback
    if quality_score >= 0.8:
        feedback = "Excellent connection! You're building deep understanding."
    elif quality_score >= 0.5:
        feedback = "Good insight! Keep making these connections."
    else:
        feedback = "Connection made! Try to expand on how the concepts relate."
    
    return ConnectionResponse(
        success=True,
        coins_earned=total_coins,
        ai_feedback=feedback,
        quality_score=quality_score
    )


@router.get("/suggested-connections")
async def get_suggested_connections(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get suggested topics to connect with"""
    from app.models.retention import UserTopicLog
    
    # Get user's learned topics
    topics = db.query(UserTopicLog).filter(
        UserTopicLog.user_id == current_user.id,
        UserTopicLog.topic_id != topic_id,
        UserTopicLog.is_active == True
    ).order_by(UserTopicLog.learned_at.desc()).limit(5).all()
    
    suggestions = [
        {
            "topic_id": t.topic_id,
            "topic_name": t.topic_name or f"Topic {t.topic_id}",
            "retention": t.retrievability,
            "days_ago": (datetime.now(timezone.utc) - t.learned_at).days if t.learned_at else 0
        }
        for t in topics
    ]
    
    return {"suggestions": suggestions}
