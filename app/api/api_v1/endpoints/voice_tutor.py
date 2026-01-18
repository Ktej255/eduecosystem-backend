from fastapi import APIRouter, Depends, HTTPException, Body
from app.api.deps import get_current_user
from app.models.user import User
from app.services.gemini_service import gemini_service
from typing import Any, Dict

router = APIRouter()

@router.post("/analyze", response_model=Dict[str, Any])
def analyze_voice_session(
    audio_base64: str = Body(..., embed=True),
    context: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Analyze a voice recording for pronunciation, tone, and confidence.
    """
    try:
        if not audio_base64:
             raise HTTPException(status_code=422, detail="Audio data is required")

        result = gemini_service.analyze_audio(audio_base64, context)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
