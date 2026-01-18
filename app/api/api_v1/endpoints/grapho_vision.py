from fastapi import APIRouter, Depends, HTTPException, Body
from app.api.deps import get_current_user
from app.models.user import User
from app.services.gemini_service import gemini_service
from typing import Any, Dict

router = APIRouter()

@router.post("/analyze-stream", response_model=Dict[str, Any])
def analyze_handwriting_stream(
    image_base64: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Analyze visual stream frame for real-time graphology insights.
    """
    try:
        if not image_base64:
             raise HTTPException(status_code=422, detail="Image data is required")

        result = gemini_service.analyze_handwriting_traits(image_base64)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
