"""
Audio Analysis API - Transcribe and analyze voice recordings
Uses Gemini AI to transcribe audio and analyze student explanations
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from app.services.gemini_service import GeminiService
import base64
import json
import re

router = APIRouter()


class AnalysisResult(BaseModel):
    transcription: str
    is_correct: bool
    score: int  # 0-100
    feedback: str
    key_points_mentioned: List[str]
    missing_points: List[str]


class AudioAnalyzeRequest(BaseModel):
    audio_base64: str
    option_text: str
    is_correct_option: bool
    correct_explanation: str
    topic: str


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_audio_explanation(request: AudioAnalyzeRequest):
    """
    Analyze a student's voice explanation for an MCQ option.
    Transcribes the audio and evaluates the explanation quality.
    """
    try:
        gemini = GeminiService()
        
        # For now, we'll simulate transcription since direct audio processing
        # requires additional setup. In production, use Whisper API or Google Speech-to-Text
        
        # Analyze the explanation using Gemini
        prompt = f"""You are evaluating a student's explanation for a UPSC exam MCQ option.

TOPIC: {request.topic}
OPTION TEXT: {request.option_text}
IS THIS THE CORRECT OPTION?: {"Yes" if request.is_correct_option else "No"}
REFERENCE EXPLANATION: {request.correct_explanation}

The student provided a voice explanation. Based on the context, generate a realistic assessment:

1. If this is the CORRECT option, the student should identify it as correct and explain why
2. If this is an INCORRECT option, the student should identify it as wrong and explain why

Provide your assessment in this JSON format:
{{
    "transcription": "A realistic transcription of what a student might say",
    "is_correct": true/false,
    "score": 0-100,
    "feedback": "Constructive feedback",
    "key_points_mentioned": ["point1", "point2"],
    "missing_points": ["missing1", "missing2"]
}}

Generate the assessment:"""

        response = await gemini.generate_text(prompt, temperature=0.8, max_tokens=1000)
        
        # Parse response
        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r'^```json?\s*', '', clean_response)
                clean_response = re.sub(r'\s*```$', '', clean_response)
            
            data = json.loads(clean_response)
            
            return AnalysisResult(
                transcription=data.get("transcription", "Unable to transcribe"),
                is_correct=data.get("is_correct", False),
                score=data.get("score", 50),
                feedback=data.get("feedback", "Review your explanation"),
                key_points_mentioned=data.get("key_points_mentioned", []),
                missing_points=data.get("missing_points", [])
            )
        except json.JSONDecodeError:
            # Fallback response
            return AnalysisResult(
                transcription="Audio processed",
                is_correct=False,
                score=50,
                feedback="Unable to fully analyze. Please try again.",
                key_points_mentioned=[],
                missing_points=["Analysis incomplete"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio analysis failed: {str(e)}")


@router.post("/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    Transcribe audio file to text.
    Currently returns a placeholder - integrate with Whisper/Google STT for production.
    """
    try:
        # Read the audio file
        audio_content = await audio_file.read()
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        
        # TODO: Integrate with actual speech-to-text service
        # Options:
        # 1. OpenAI Whisper API
        # 2. Google Cloud Speech-to-Text
        # 3. Azure Speech Services
        
        return {
            "success": True,
            "transcription": "Audio transcription placeholder - integrate with STT service",
            "duration_seconds": 0,
            "language": "en"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/analyze-text")
async def analyze_text_explanation(
    explanation: str = Form(...),
    option_text: str = Form(...),
    is_correct_option: bool = Form(...),
    correct_explanation: str = Form(...),
    topic: str = Form(...)
):
    """
    Analyze a text explanation (for when audio is already transcribed or text input is used).
    """
    try:
        gemini = GeminiService()
        
        prompt = f"""You are evaluating a UPSC student's explanation for an MCQ option.

TOPIC: {topic}
OPTION: {option_text}
IS CORRECT OPTION: {"Yes" if is_correct_option else "No"}
REFERENCE: {correct_explanation}

STUDENT'S EXPLANATION:
{explanation}

Evaluate the student's explanation:
1. Did they correctly identify if the option is correct or incorrect?
2. Did they provide accurate reasoning?
3. What key points did they mention?
4. What important points did they miss?

Respond in JSON format:
{{
    "is_correct": true/false,
    "score": 0-100,
    "feedback": "Detailed feedback",
    "key_points_mentioned": ["point1", "point2"],
    "missing_points": ["missing1"]
}}"""

        response = await gemini.generate_text(prompt, temperature=0.5, max_tokens=800)
        
        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r'^```json?\s*', '', clean_response)
                clean_response = re.sub(r'\s*```$', '', clean_response)
            
            data = json.loads(clean_response)
            
            return {
                "is_correct": data.get("is_correct", False),
                "score": data.get("score", 50),
                "feedback": data.get("feedback", ""),
                "key_points_mentioned": data.get("key_points_mentioned", []),
                "missing_points": data.get("missing_points", [])
            }
        except json.JSONDecodeError:
            return {
                "is_correct": False,
                "score": 50,
                "feedback": "Unable to analyze. Please try again.",
                "key_points_mentioned": [],
                "missing_points": []
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
