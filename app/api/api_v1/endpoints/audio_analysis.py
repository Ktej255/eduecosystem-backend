from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.services.gemini_service import gemini_service
import base64
from app.api import deps
from app.models.user import User
from typing import Optional
from pydantic import BaseModel

router = APIRouter()


class FlashcardAnalysisRequest(BaseModel):
    """Request model for flashcard audio analysis via JSON"""
    audio_base64: str
    card_front: str
    card_back: str
    topic: str = ""
    chapter_content: Optional[str] = None  # Full chapter content for comprehensive validation


@router.post("/analyze-flashcard")
async def analyze_flashcard_json(
    request: FlashcardAnalysisRequest,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Analyze student's audio recall for a flashcard using JSON payload.
    
    1. Transcribes audio using Gemini.
    2. Compares transcription with expected answer AND chapter content (if provided).
    3. Returns score, feedback, and missing points.
    """
    try:
        # 1. Decode Audio from Base64
        audio_data = request.audio_base64
        
        # Remove data URL prefix if present
        if "," in audio_data:
            audio_data = audio_data.split(",")[1]
        
        # 2. Transcribe
        transcript = gemini_service.transcribe_audio(audio_data)
        
        if not transcript or transcript.strip() == "":
            return {
                "transcription": "",
                "is_correct": False,
                "score": 0,
                "feedback": "Could not transcribe audio. Please speak clearly and try again.",
                "key_points_mentioned": [],
                "missing_points": []
            }
        
        # 3. Analyze Recall with comprehensive prompt
        if request.chapter_content:
            # Use chapter content for more comprehensive evaluation
            analysis = evaluate_with_chapter_content(
                question=request.card_front,
                flashcard_answer=request.card_back,
                chapter_content=request.chapter_content,
                student_answer=transcript,
                topic=request.topic
            )
        else:
            # Fallback to standard evaluation
            analysis = gemini_service.evaluate_recall(
                original_text=request.card_back,
                student_recall=transcript
            )
        
        # Build response
        return {
            "transcription": transcript,
            "is_correct": analysis.get("is_correct", analysis.get("score", 0) >= 70),
            "score": analysis.get("score", 0),
            "feedback": analysis.get("feedback", ""),
            "key_points_mentioned": analysis.get("key_points_mentioned", []),
            "missing_points": analysis.get("missing_points", [])
        }

    except Exception as e:
        print(f"Error in analyze_flashcard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def evaluate_with_chapter_content(
    question: str, 
    flashcard_answer: str, 
    chapter_content: str, 
    student_answer: str,
    topic: str
) -> dict:
    """
    Evaluate student's answer against both the flashcard answer and the full chapter content.
    This provides more flexibility as students may express concepts differently.
    """
    
    prompt = f"""You are an expert examiner evaluating a student's verbal explanation of an Indian Polity concept.

**Question Asked:**
{question}

**Expected Key Points (from flashcard):**
{flashcard_answer}

**Full Chapter Context (for reference):**
{chapter_content[:8000]}  # Limit to avoid token overflow

**Student's Verbal Answer:**
"{student_answer}"

**Topic:** {topic}

**Evaluation Instructions:**
1. The student's answer does NOT need to match word-for-word with the flashcard answer.
2. Evaluate based on conceptual understanding and key points coverage.
3. Use the chapter content as additional context - if the student mentions related valid points from the chapter that aren't in the flashcard, give them credit.
4. Be lenient with phrasing but strict with factual accuracy.

**Please evaluate and provide:**

1. **Score (0-100):** 
   - 90-100: Excellent, covers all/most key points accurately
   - 70-89: Good, covers majority of important concepts
   - 50-69: Partial understanding, missing significant points
   - Below 50: Needs improvement, major gaps in understanding

2. **Key Points Mentioned:** List the correct concepts the student explained

3. **Missing Points:** Important concepts the student missed

4. **Feedback:** Brief, encouraging feedback (2-3 sentences)

5. **Is Correct:** true if score >= 70, false otherwise

Respond in JSON format:
{{
    "score": <number>,
    "is_correct": <boolean>,
    "key_points_mentioned": ["point1", "point2", ...],
    "missing_points": ["point1", "point2", ...],
    "feedback": "<feedback text>"
}}"""

    try:
        result = gemini_service.generate_content(prompt)
        
        # Parse JSON response
        import json
        import re
        
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            analysis = json.loads(json_match.group())
            return analysis
        else:
            # Fallback if parsing fails
            return {
                "score": 60,
                "is_correct": False,
                "key_points_mentioned": [],
                "missing_points": ["Could not parse analysis"],
                "feedback": "Your answer was recorded. Please review the correct answer."
            }
    except Exception as e:
        print(f"Error in evaluate_with_chapter_content: {e}")
        return {
            "score": 50,
            "is_correct": False,
            "key_points_mentioned": [],
            "missing_points": [],
            "feedback": "Analysis could not be completed. Please try again."
        }


@router.post("/analyze-flashcard-form")
async def analyze_flashcard(
    audio: UploadFile = File(...),
    question: str = Form(...),
    expected_answer: str = Form(...),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Analyze student's audio recall for a flashcard (Form/File upload version).
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
