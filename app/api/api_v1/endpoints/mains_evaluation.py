"""
Mains Answer Evaluation API Endpoint
Uses GeminiService for AI-powered UPSC Mains answer evaluation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from app.services.gemini_service import gemini_service
import json
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class MainsEvaluationRequest(BaseModel):
    question: str = Field(..., description="The Mains question text")
    answer: str = Field(..., description="Student's answer text")
    model_answer: Optional[str] = Field(None, description="Optional model answer for reference")
    marks: int = Field(10, description="Maximum marks for the question")


class MainsEvaluationResponse(BaseModel):
    score: int = Field(..., description="Score awarded (0 to marks)")
    feedback: str = Field(..., description="Overall assessment")
    strengths: List[str] = Field(default_factory=list, description="Strong points in the answer")
    improvements: List[str] = Field(default_factory=list, description="Areas for improvement")


@router.post("/evaluate", response_model=MainsEvaluationResponse)
async def evaluate_mains_answer(request: MainsEvaluationRequest):
    """
    Evaluate a student's Mains answer using AI.
    
    Returns a score, feedback, strengths, and improvements.
    """
    
    model_answer_section = f"""
MODEL ANSWER (Reference):
{request.model_answer}
""" if request.model_answer else ""

    prompt = f"""You are an expert UPSC Mains evaluator. Evaluate the following answer based on:
1. Relevance to the question
2. Structure (Introduction, Body with multiple points, Conclusion)
3. Use of keywords, examples, and data points
4. Factual accuracy
5. Answer length appropriateness for the marks

QUESTION ({request.marks} Marks):
{request.question}

STUDENT'S ANSWER:
{request.answer}
{model_answer_section}

IMPORTANT: Return ONLY valid JSON in this exact format, no other text:
{{
    "score": <number between 0 and {request.marks}>,
    "feedback": "<2-3 sentence overall assessment>",
    "strengths": ["<strength 1>", "<strength 2>"],
    "improvements": ["<improvement 1>", "<improvement 2>"]
}}
"""

    try:
        response_text = gemini_service.generate_text(
            prompt=prompt,
            is_complex=True,
            temperature=0.3
        )
        
        # Clean and parse JSON
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        
        # Try to extract JSON from response
        json_match = re.search(r"\{.*\}", clean_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in response")
        
        # Validate and clamp score
        score = max(0, min(request.marks, int(data.get("score", 0))))
        
        return MainsEvaluationResponse(
            score=score,
            feedback=data.get("feedback", "Evaluation completed."),
            strengths=data.get("strengths", []),
            improvements=data.get("improvements", [])
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}. Response: {response_text[:200]}")
        raise HTTPException(status_code=500, detail="AI response parsing failed. Please try again.")
    except Exception as e:
        logger.error(f"Mains evaluation error: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
