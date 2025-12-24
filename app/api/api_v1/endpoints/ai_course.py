"""
AI Course Generation API Endpoints
Integrates Genkit flows for AI-powered course creation
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api import deps
from app.models.user import User
import httpx
import os

router = APIRouter()

# Genkit server URL (assuming Genkit runs on port 3400)
GENKIT_URL = os.getenv("GENKIT_URL", "http://localhost:3400")


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================


class CourseOutlineRequest(BaseModel):
    topic: str
    target_audience: str = "General learners"
    difficulty: str = "beginner"
    objectives: str = ""
    module_count: int = 4


class LessonSchema(BaseModel):
    title: str
    description: str
    type: str
    duration_minutes: int


class ModuleSchema(BaseModel):
    title: str
    description: str
    lessons: List[LessonSchema]


class CourseOutlineResponse(BaseModel):
    course_title: str
    course_description: str
    modules: List[ModuleSchema]


class GenerateLessonContentRequest(BaseModel):
    lesson_title: str
    module_title: str
    course_context: str = ""
    lesson_type: str = "text"
    duration: int = 15


class LessonContentResponse(BaseModel):
    content: str


class GenerateQuizRequest(BaseModel):
    module_title: str
    lesson_titles: List[str]
    course_context: str = ""


class QuizQuestion(BaseModel):
    text: str
    options: List[str]
    correct_answer: str
    explanation: str = ""


class QuizResponse(BaseModel):
    questions: List[QuizQuestion]


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/generate-outline", response_model=CourseOutlineResponse)
async def generate_course_outline(
    request: CourseOutlineRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Generate a complete course outline using Gemini AI

    - **topic**: Course topic or subject
    - **target_audience**: Who the course is for
    - **difficulty**: beginner, intermediate, or advanced
    - **objectives**: Learning objectives
    - **module_count**: Number of modules to generate (default 4)
    """
    try:
        from app.services.gemini_service import GeminiService
        import json

        gemini = GeminiService()

        # Build comprehensive prompt
        prompt = f"""You are an expert course designer. Create a detailed course outline for:

Title: {request.topic}
Target Audience: {request.target_audience}
Difficulty Level: {request.difficulty}
Number of Modules: {request.module_count}
"""

        if request.objectives:
            prompt += f"\nLearning Objectives: {request.objectives}"

        prompt += f"""

Generate a comprehensive course structure with EXACTLY {request.module_count} modules. Each module should have 3-5 lessons.

Return ONLY a valid JSON object in this exact format:
{{
  "course_title": "{request.topic}",
  "course_description": "Brief course description",
  "modules": [
    {{
      "title": "Module 1 Title",
      "description": "Module description",
      "lessons": [
        {{
          "title": "Lesson Title",
          "description": "Lesson content description",
          "type": "text",
          "duration_minutes": 30
        }}
      ]
    }}
  ]
}}

For lesson types, use: "text", "video", "quiz", or "assignment"
Return ONLY the JSON, no markdown, no explanations."""

        # Get AI response
        response_text = gemini.generate_text(
            prompt, 
            user=current_user, 
            is_complex=True
        )

        # Parse JSON
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        outline_data = json.loads(response_text)

        return CourseOutlineResponse(**outline_data)

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        # Return fallback
        return CourseOutlineResponse(
            course_title=request.topic,
            course_description=f"A comprehensive {request.difficulty} course on {request.topic}",
            modules=[
                ModuleSchema(
                    title=f"Module {i + 1}: Introduction to {request.topic}",
                    description="Learn the fundamentals",
                    lessons=[
                        LessonSchema(
                            title=f"Lesson {j + 1}",
                            description="Core concepts and practical examples",
                            type="text",
                            duration_minutes=25,
                        )
                        for j in range(3)
                    ],
                )
                for i in range(request.module_count)
            ],
        )
    except Exception as e:
        print(f"Error generating outline: {e}")
        raise HTTPException(
            status_code=500,
            detail="Could not generate course outline. Please try manual course creation instead.",
        )


@router.post("/generate-lesson-content", response_model=LessonContentResponse)
async def generate_lesson_content(
    request: GenerateLessonContentRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Generate content for a specific lesson using AI

    - **lesson_title**: Title of the lesson
    - **module_title**: Parent module title for context
    - **course_context**: Brief description of the course
    - **lesson_type**: text, video, quiz, or assignment
    - **duration**: Target duration in minutes
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GENKIT_URL}/generateLessonContent",
                json={
                    "lessonTitle": request.lesson_title,
                    "moduleTitle": request.module_title,
                    "courseContext": request.course_context,
                    "lessonType": request.lesson_type,
                    "duration": request.duration,
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Content generation failed: {response.text}",
                )

            result = response.json()
            return LessonContentResponse(content=result.get("content", ""))

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, detail=f"Could not connect to AI service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Content generation failed: {str(e)}"
        )


@router.post("/generate-module-quiz", response_model=QuizResponse)
async def generate_module_quiz(
    request: GenerateQuizRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Generate quiz questions for an entire module

    - **module_title**: Title of the module
    - **lesson_titles**: List of lesson titles in the module
    - **course_context**: Brief course description for context
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GENKIT_URL}/generateModuleQuiz",
                json={
                    "moduleTitle": request.module_title,
                    "lessonTitles": request.lesson_titles,
                    "courseContext": request.course_context,
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500, detail=f"Quiz generation failed: {response.text}"
                )

            result = response.json()
            return QuizResponse(
                questions=[
                    QuizQuestion(
                        text=q["text"],
                        options=q["options"],
                        correct_answer=q["correctAnswer"],
                        explanation=q.get("explanation", ""),
                    )
                    for q in result.get("questions", [])
                ]
            )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, detail=f"Could not connect to AI service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")
