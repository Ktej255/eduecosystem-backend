"""
Content Generator API - AI-powered flashcard and MCQ generation
Generates UPSC Prelims level content from topic text using Gemini AI
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.services.gemini_service import GeminiService
import json
import re

router = APIRouter()

# Request/Response Models
class FlashcardGenerateRequest(BaseModel):
    topic_title: str
    topic_content: str
    num_cards: int = 10
    difficulty: str = "upsc_prelims"  # upsc_prelims, upsc_mains, beginner

class Flashcard(BaseModel):
    front: str
    back: str
    category: str  # concept, fact, article, date

class FlashcardGenerateResponse(BaseModel):
    topic: str
    flashcards: List[Flashcard]
    generated_count: int

class MCQGenerateRequest(BaseModel):
    topic_title: str
    topic_content: str
    num_questions: int = 5
    difficulty: str = "upsc_prelims"
    include_explanations: bool = True

class MCQOption(BaseModel):
    text: str
    is_correct: bool
    explanation: str

class MCQ(BaseModel):
    question: str
    options: List[MCQOption]
    correct_answer_index: int
    topic: str
    difficulty: str

class MCQGenerateResponse(BaseModel):
    topic: str
    questions: List[MCQ]
    generated_count: int


@router.post("/flashcards", response_model=FlashcardGenerateResponse)
async def generate_flashcards(request: FlashcardGenerateRequest):
    """
    Generate flashcards from topic content using Gemini AI.
    Flashcards are tailored for UPSC Prelims preparation.
    """
    try:
        gemini = GeminiService()
        
        prompt = f"""You are an expert UPSC Civil Services exam coach. Generate exactly {request.num_cards} flashcards from the following topic content.

TOPIC: {request.topic_title}

CONTENT:
{request.topic_content}

REQUIREMENTS:
1. Each flashcard should test ONE key concept, fact, article, or date
2. Front side should be a clear question or prompt
3. Back side should be a concise, accurate answer
4. Focus on facts that are frequently asked in UPSC Prelims
5. Include Constitutional articles, important dates, key terms
6. Vary the types: some factual recall, some conceptual understanding

OUTPUT FORMAT (respond with ONLY valid JSON, no markdown):
{{
  "flashcards": [
    {{"front": "Question or prompt", "back": "Answer", "category": "concept|fact|article|date"}},
    ...
  ]
}}

Generate exactly {request.num_cards} flashcards now:"""

        response = await gemini.generate_text(prompt, temperature=0.7, max_tokens=3000)
        
        # Parse the JSON response
        try:
            # Clean up response - remove markdown if present
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r'^```json?\s*', '', clean_response)
                clean_response = re.sub(r'\s*```$', '', clean_response)
            
            data = json.loads(clean_response)
            flashcards = [
                Flashcard(
                    front=card.get("front", ""),
                    back=card.get("back", ""),
                    category=card.get("category", "concept")
                )
                for card in data.get("flashcards", [])
            ]
        except json.JSONDecodeError:
            # Fallback: create basic flashcards from content
            flashcards = [
                Flashcard(
                    front=f"What is the key concept of {request.topic_title}?",
                    back="Review the topic content for detailed understanding.",
                    category="concept"
                )
            ]
        
        return FlashcardGenerateResponse(
            topic=request.topic_title,
            flashcards=flashcards,
            generated_count=len(flashcards)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {str(e)}")


@router.post("/mcqs", response_model=MCQGenerateResponse)
async def generate_mcqs(request: MCQGenerateRequest):
    """
    Generate UPSC Prelims level MCQs from topic content using Gemini AI.
    Includes detailed explanations for each option.
    """
    try:
        gemini = GeminiService()
        
        prompt = f"""You are an expert UPSC Civil Services exam question setter. Generate exactly {request.num_questions} high-quality MCQs from the following topic content.

TOPIC: {request.topic_title}

CONTENT:
{request.topic_content}

REQUIREMENTS:
1. Questions should be at UPSC Prelims level
2. Each question must have exactly 4 options
3. Include statement-based questions (common in UPSC)
4. Test factual accuracy, conceptual understanding, and application
5. Provide detailed explanation for EACH option (why correct/incorrect)
6. Include tricky options that test deep understanding
7. Cover different aspects of the topic

QUESTION TYPES TO INCLUDE:
- "Which of the following statements is/are correct?"
- "Consider the following statements... How many are correct?"
- Direct factual questions
- Conceptual questions

OUTPUT FORMAT (respond with ONLY valid JSON, no markdown):
{{
  "questions": [
    {{
      "question": "Question text",
      "options": [
        {{"text": "Option A", "is_correct": false, "explanation": "Why this is incorrect"}},
        {{"text": "Option B", "is_correct": true, "explanation": "Why this is correct"}},
        {{"text": "Option C", "is_correct": false, "explanation": "Why this is incorrect"}},
        {{"text": "Option D", "is_correct": false, "explanation": "Why this is incorrect"}}
      ],
      "correct_answer_index": 1
    }},
    ...
  ]
}}

Generate exactly {request.num_questions} MCQs now:"""

        response = await gemini.generate_text(prompt, temperature=0.7, max_tokens=4000)
        
        # Parse the JSON response
        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r'^```json?\s*', '', clean_response)
                clean_response = re.sub(r'\s*```$', '', clean_response)
            
            data = json.loads(clean_response)
            questions = []
            
            for q in data.get("questions", []):
                options = [
                    MCQOption(
                        text=opt.get("text", ""),
                        is_correct=opt.get("is_correct", False),
                        explanation=opt.get("explanation", "")
                    )
                    for opt in q.get("options", [])
                ]
                
                # Find correct answer index
                correct_idx = next(
                    (i for i, opt in enumerate(options) if opt.is_correct),
                    0
                )
                
                questions.append(MCQ(
                    question=q.get("question", ""),
                    options=options,
                    correct_answer_index=correct_idx,
                    topic=request.topic_title,
                    difficulty=request.difficulty
                ))
        except json.JSONDecodeError:
            # Fallback: create sample question
            questions = [
                MCQ(
                    question=f"Which of the following is true about {request.topic_title}?",
                    options=[
                        MCQOption(text="Option A", is_correct=False, explanation="Incorrect"),
                        MCQOption(text="Option B", is_correct=True, explanation="Correct"),
                        MCQOption(text="Option C", is_correct=False, explanation="Incorrect"),
                        MCQOption(text="Option D", is_correct=False, explanation="Incorrect"),
                    ],
                    correct_answer_index=1,
                    topic=request.topic_title,
                    difficulty=request.difficulty
                )
            ]
        
        return MCQGenerateResponse(
            topic=request.topic_title,
            questions=questions,
            generated_count=len(questions)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate MCQs: {str(e)}")


@router.post("/from-video-url")
async def generate_content_from_video(
    video_url: str,
    topic_title: str,
    generate_flashcards: bool = True,
    generate_mcqs: bool = True,
    num_flashcards: int = 10,
    num_mcqs: int = 5
):
    """
    Generate flashcards and MCQs from a video URL.
    Note: This currently uses the topic title as context.
    Full video transcription would require YouTube API integration.
    """
    # For now, generate based on topic title only
    # In future, integrate with YouTube transcript API
    
    results = {
        "video_url": video_url,
        "topic": topic_title,
        "flashcards": None,
        "mcqs": None
    }
    
    sample_content = f"""
    This is an educational video about {topic_title}.
    The video covers key concepts, important facts, and exam-relevant points.
    """
    
    if generate_flashcards:
        flashcard_request = FlashcardGenerateRequest(
            topic_title=topic_title,
            topic_content=sample_content,
            num_cards=num_flashcards
        )
        results["flashcards"] = await generate_flashcards(flashcard_request)
    
    if generate_mcqs:
        mcq_request = MCQGenerateRequest(
            topic_title=topic_title,
            topic_content=sample_content,
            num_questions=num_mcqs
        )
        results["mcqs"] = await generate_mcqs(mcq_request)
    
    return results
