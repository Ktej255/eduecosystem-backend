from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.services.gemini_service import gemini_service
from pydantic import BaseModel
import random

router = APIRouter()

class NewsQuizRequest(BaseModel):
    topic_focus: str = "General"

@router.post("/news-quiz")
def generate_news_quiz(
    request: NewsQuizRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Generates a Daily News Quiz based on mocked headlines (simulating a scraper).
    """
    
    # Mock Real-Time Headlines (In prod, fetch from NewsAPI)
    headlines = [
        "RBI keeps repo rate unchanged at 6.5% for the seventh consecutive time",
        "India and EFTA sign Trade and Economic Partnership Agreement (TEPA)",
        "Supreme Court strikes down Electoral Bonds scheme as unconstitutional",
        "ISRO successfully conducts landing experiment of RLV-LEX-02",
        "Centre notifies Rules for Citizenship Amendment Act (CAA), 2019"
    ]
    
    # Randomize to simulate daily changes
    selected_headlines = random.sample(headlines, 3)
    
    prompt = f"""Generate 5 UPSC-style MCQs based on these news headlines:
HEADLINES:
{", ".join(selected_headlines)}

Return JSON ONLY in this format:
[
    {{
        "id": 1,
        "question": "Question text...",
        "options": ["A", "B", "C", "D"],
        "correctIndex": 0,
        "explanation": "Why it is correct..."
    }}
]
"""
    try:
        response_text = gemini_service.generate_text(prompt, user=current_user, temperature=0.7, is_complex=True)
        # Parse JSON
        import json
        clean = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        return data
    except Exception as e:
        print(f"News Quiz Error: {e}")
        # Fallback static quiz
        return [
            {
                "id": 1, 
                "question": "Which organization regulates the Repo Rate in India?",
                "options": ["SEBI", "RBI", "Finance Ministry", "NITI Aayog"],
                "correctIndex": 1,
                "explanation": "RBI Monetary Policy Committee decides the repo rate."
            }
        ]
