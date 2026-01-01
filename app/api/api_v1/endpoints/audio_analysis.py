from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.services.gemini_service import gemini_service
import base64
from app.api import deps
from app.models.user import User

router = APIRouter()

@router.post("/analyze-flashcard")
async def analyze_flashcard(
    audio: UploadFile = File(...),
    question: str = Form(...),
    expected_answer: str = Form(...),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Analyze student's audio recall for a flashcard.
    1. Transcribes audio using Gemini.
    2. Compares transcription with expected answer.
    3. Returns score, feedback, and missing points.
    """
    try:
        # 1. Read Audio
        audio_content = await audio.read()
        if not audio_content:
            raise HTTPException(status_code=400, detail="Empty audio file")
            
        # Convert to Base64 for Gemini
        audio_b64 = base64.b64encode(audio_content).decode("utf-8")
        
        # 2. Transcribe
        transcript = gemini_service.transcribe_audio(audio_b64)
        
        # 3. Analyze Recall
        # Combine Question + Answer for context if needed, but evaluate_recall expects "original_text"
        # We pass expected_answer as original_text
        
        analysis = gemini_service.evaluate_recall(
            original_text=expected_answer,
            student_recall=transcript
        )
        
        # Add transcript to result
        analysis["transcript"] = transcript
        
        return analysis

    except Exception as e:
        print(f"Error in analyze_flashcard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
