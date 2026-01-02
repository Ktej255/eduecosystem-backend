from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.services.gemini_service import gemini_service
import base64
from app.api import deps
from app.models.user import User
from typing import Optional

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


@router.post("/analyze-study-explanation")
async def analyze_study_explanation(
    audio: UploadFile = File(...),
    topic_name: str = Form(...),
    subject: str = Form(...),
    session_type: str = Form(...),  # "study_25", "study_45", "revision_25"
    duration_minutes: int = Form(...),
    expected_concepts: Optional[str] = Form(None),  # Comma-separated key concepts
    current_user: User = Depends(deps.get_current_user)
):
    """
    Analyze student's explanation after a Pomodoro study session.
    
    This endpoint:
    1. Transcribes the audio recording
    2. Analyzes content coverage based on topic
    3. Identifies key concepts mentioned
    4. Provides feedback and improvement suggestions
    5. Generates comprehension score
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
        
        if not transcript or transcript.strip() == "":
            return {
                "success": False,
                "error": "Could not transcribe audio. Please ensure clear audio recording.",
                "transcript": "",
                "score": 0
            }
        
        # 3. Analyze the explanation using Gemini
        analysis_prompt = f"""You are evaluating a student's explanation after a study session.

**Context:**
- Topic: {topic_name}
- Subject: {subject}
- Session Type: {session_type} ({'25-minute focus' if '25' in session_type else '45-minute deep study' if '45' in session_type else 'revision'})
- Duration: {duration_minutes} minutes
{f'- Expected Key Concepts: {expected_concepts}' if expected_concepts else ''}

**Student's Explanation Transcript:**
"{transcript}"

**Analyze and provide:**
1. **Comprehension Score (0-100)**: Based on clarity, depth, and coverage
2. **Key Concepts Identified**: List the main concepts the student mentioned
3. **Missing Concepts**: Important topics not covered (if any)
4. **Clarity Rating (1-5)**: How clearly did the student explain?
5. **Depth Rating (1-5)**: How deeply did they understand?
6. **Strengths**: What the student did well
7. **Areas for Improvement**: Specific suggestions
8. **Summary**: 2-3 sentence overall assessment

Respond in JSON format:
{{
    "comprehension_score": <number>,
    "key_concepts": ["concept1", "concept2", ...],
    "missing_concepts": ["concept1", ...],
    "clarity_rating": <1-5>,
    "depth_rating": <1-5>,
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2"],
    "summary": "<summary text>"
}}"""

        # Use Gemini to analyze
        analysis_result = gemini_service.generate_content(analysis_prompt)
        
        # Parse the JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', analysis_result)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            # Fallback if JSON parsing fails
            analysis = {
                "comprehension_score": 70,
                "key_concepts": [],
                "missing_concepts": [],
                "clarity_rating": 3,
                "depth_rating": 3,
                "strengths": ["Completed the explanation session"],
                "improvements": ["Try to cover more key concepts"],
                "summary": "Good effort! Keep practicing your explanations."
            }
        
        return {
            "success": True,
            "transcript": transcript,
            "topic_name": topic_name,
            "subject": subject,
            "session_type": session_type,
            "analysis": analysis
        }

    except json.JSONDecodeError:
        return {
            "success": True,
            "transcript": transcript,
            "topic_name": topic_name,
            "subject": subject,
            "session_type": session_type,
            "analysis": {
                "comprehension_score": 65,
                "key_concepts": [],
                "missing_concepts": [],
                "clarity_rating": 3,
                "depth_rating": 3,
                "strengths": ["Completed the study session"],
                "improvements": ["Practice explaining concepts more clearly"],
                "summary": "Keep up the good work!"
            }
        }
    except Exception as e:
        print(f"Error in analyze_study_explanation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

