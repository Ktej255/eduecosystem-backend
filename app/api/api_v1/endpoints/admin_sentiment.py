from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, List
from datetime import date

from app.api import deps
from app.services.sentiment_service import sentiment_service
from app.models.user import User

router = APIRouter()

@router.get("/vibe-pulse", response_model=dict)
async def get_vibe_pulse(
    batch_name: str = Query("Global"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Get the latest aggregated sentiment for a batch.
    """
    # Trigger aggregation for today if it doesn't exist (can also be a background task)
    latest = await sentiment_service.aggregate_daily_sentiment(db, batch_name)
    
    if not latest:
        # Check if we have one for yesterday or just return default
        latest = sentiment_service.get_sentiment_trends(db, batch_name, limit=1)
        if latest:
            latest = latest[0]
            
    if not latest:
        return {
            "focused_score": 0.5,
            "anxious_score": 0.2,
            "tired_score": 0.1,
            "inspired_score": 0.6,
            "dominant_vibe": "Focused",
            "top_keywords": "Learning, Sadhana",
            "sample_size": 0
        }
        
    return {
        "focused_score": latest.focused_score,
        "anxious_score": latest.anxious_score,
        "tired_score": latest.tired_score,
        "inspired_score": latest.inspired_score,
        "dominant_vibe": latest.dominant_vibe,
        "top_keywords": latest.top_keywords,
        "sample_size": latest.sample_size
    }

@router.get("/trends", response_model=List[dict])
def get_sentiment_trends(
    batch_name: str = Query("Global"),
    days: int = Query(7),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Get sentiment trends for the last X days.
    """
    trends = sentiment_service.get_sentiment_trends(db, batch_name, days=days)
    return [
        {
            "date": t.date.isoformat(),
            "focused": t.focused_score,
            "anxious": t.anxious_score,
            "tired": t.tired_score,
            "inspired": t.inspired_score
        }
        for t in trends
    ]
