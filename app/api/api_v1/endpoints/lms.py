from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.services.gemini_service import gemini_service
import json

router = APIRouter()


@router.post("/quiz/generate")
def generate_quiz(
    topic: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Generate an AI-powered quiz for a topic using Gemini.
    """
    from app.models.quiz import Quiz, Question

    # Create quiz record
    quiz = Quiz(title=f"Quiz on {topic}", topic=topic, user_id=current_user.id)
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    # Use Gemini to generate quiz questions
    try:
        quiz_prompt = f"""Generate 5 multiple-choice quiz questions about {topic}.

For each question, provide:
- The question text
- 4 answer options (A, B, C, D)
- The correct answer

Format as JSON array:
[
  {{
    "text": "question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": "Option A"
  }},
  ...
]

Make questions educational, clear, and appropriately challenging."""

        gemini_response = gemini_service.generate_text(
            prompt=quiz_prompt, 
            user=current_user,
            is_complex=True,
            temperature=0.7, 
            max_tokens=1500
        )

        # Try to parse JSON from response
        try:
            # Extract JSON from response (Gemini might wrap it in markdown)
            json_start = gemini_response.find("[")
            json_end = gemini_response.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                json_str = gemini_response[json_start:json_end]
                quiz_questions = json.loads(json_str)
            else:
                raise ValueError("No JSON array found in response")
        except Exception as e:
            print(f"JSON parsing error: {e}")
            # Fallback to mock questions if JSON parsing fails
            quiz_questions = [
                {
                    "text": f"What is a key concept in {topic}?",
                    "options": ["Concept A", "Concept B", "Concept C", "Concept D"],
                    "correct": "Concept A",
                },
                {
                    "text": f"Which principle is important in {topic}?",
                    "options": [
                        "Principle X",
                        "Principle Y",
                        "Principle Z",
                        "All of the above",
                    ],
                    "correct": "All of the above",
                },
            ]

    except Exception as e:
        print(f"Gemini Quiz Generation Error: {e}")
        # Fallback to mock questions if Gemini fails
        quiz_questions = [
            {
                "text": f"What is a key event in {topic}?",
                "options": ["Event A", "Event B", "Event C", "Event D"],
                "correct": "Event A",
            },
            {
                "text": f"Who is a famous figure in {topic}?",
                "options": ["Person X", "Person Y", "Person Z", "Person W"],
                "correct": "Person X",
            },
        ]

    # Save questions to database
    for q in quiz_questions:
        question = Question(
            quiz_id=quiz.id,
            text=q["text"],
            options=json.dumps(q["options"]),
            correct_answer=q["correct"],
        )
        db.add(question)

    db.commit()

    return {"quiz_id": quiz.id, "title": quiz.title, "questions": quiz_questions}
