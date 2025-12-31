
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.ai_router import ai_router
from app.api.deps import get_current_user, get_db
from sqlalchemy.orm import Session
from app.models.user import User
from datetime import datetime
import json

router = APIRouter()

class NotesToMCQRequest(BaseModel):
    notes_text: str
    num_questions: int = 5
    difficulty: str = "hard"  # easy, medium, hard, upsc-level

class MCQOption(BaseModel):
    id: str  # A, B, C, D
    text: str

class MCQItem(BaseModel):
    question: str
    options: List[MCQOption]
    correct_option_id: str
    explanation: str

class MCQGeneratorResponse(BaseModel):
    source_topic: str
    questions: List[MCQItem]

SYSTEM_PROMPT = """You are an expert UPSC Exam Question Generator.
Your task is to generate high-quality Multiple Choice Questions (MCQs) based STRICTLY on the provided text.

RULES:
1. Questions must be challenging and conceptual.
2. Distractors (wrong answers) must be plausible.
3. Include a detailed explanation for the correct answer.
4. Output specific JSON format only.

FORMAT:
{
  "source_topic": "Inferred Topic Name",
  "questions": [
    {
      "question": "Question text here?",
      "options": [
        {"id": "A", "text": "Option A text"},
        {"id": "B", "text": "Option B text"},
        {"id": "C", "text": "Option C text"},
        {"id": "D", "text": "Option D text"}
      ],
      "correct_option_id": "B",
      "explanation": "Detailed explanation why B is correct and others are wrong."
    }
  ]
}
"""

@router.post("/generate-mcq", response_model=MCQGeneratorResponse)
async def generate_mcq_from_notes(
    request: NotesToMCQRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate MCQs from studen notes or pasted text.
    """
    if len(request.notes_text) < 50:
        raise HTTPException(status_code=400, detail="Text too short. Please provide meaningful notes.")

    prompt = f"""
    GENERATE {request.num_questions} {request.difficulty} MCQs based on the following notes:
    
    --- START NOTES ---
    {request.notes_text[:4000]} 
    --- END NOTES ---
    
    Ensure the questions follow UPSC standards (conceptual, statement-based if applicable).
    """

    try:
        result = await ai_router.route(
            prompt=prompt,
            system_message=SYSTEM_PROMPT,
            max_tokens=2000,
            temperature=0.7,
            is_complex=True
        )
        
        content = result["content"]
        # Basic JSON parsing cleanup
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        
        data = json.loads(content)
        return data

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI produced invalid JSON. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- COACHING SESSION ENDPOINTS ---

class StartCoachingRequest(BaseModel):
    topic: str
    context_data: dict = {}

class ChatRequest(BaseModel):
    session_id: int
    message: str

class CoachingResponse(BaseModel):
    session_id: int
    message: str
    role: str

@router.post("/start-coaching", response_model=CoachingResponse)
async def start_coaching(
    request: StartCoachingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)  # Need to import Session and get_db
):
    """
    Start a new AI coaching session.
    """
    from app.models.ai_coaching import CoachingSession
    from datetime import datetime

    session = CoachingSession(
        user_id=current_user.id,
        topic=request.topic,
        context_data=request.context_data,
        messages=[
            {"role": "system", "content": f"You are an expert AI Coach for UPSC aspirants. Your goal is to help the student master the topic '{request.topic}'. Be encouraging, Socratic, and precise. If they are wrong, correct them gently but firmly. Keep responses concise."}
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Generate initial greeting
    greeting = f"Hello! I'm your AI Coach for {request.topic}. How can I help you today?"
    session.messages.append({"role": "assistant", "content": greeting})
    
    # Force update messages list (SQLAlchemy JSON mutation tracking sometimes needs this)
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(session, "messages")
    
    db.commit()

    return {
        "session_id": session.id,
        "message": greeting,
        "role": "assistant"
    }

@router.post("/chat-with-coach", response_model=CoachingResponse)
async def chat_with_coach(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message to the AI coach and get a response.
    """
    from app.models.ai_coaching import CoachingSession
    from sqlalchemy.orm.attributes import flag_modified
    
    session = db.query(CoachingSession).filter(
        CoachingSession.id == request.session_id,
        CoachingSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Coaching session not found")

    # Append user message
    session.messages.append({"role": "user", "content": request.message})
    flag_modified(session, "messages")
    db.commit() # Save user message first

    # Prepare context for AI (limit history to last 10 messages for cost)
    conversation_history = session.messages[-10:]
    
    # Construct prompt from history
    system_msg = session.messages[0]["content"]  # Preserved system prompt
    
    # We strip the system prompt from history if it's there to strictly follow ai_router format 
    # (though ai_router takes system_message separately)
    chat_history_text = ""
    for msg in conversation_history:
        if msg["role"] != "system":
            chat_history_text += f"{msg['role'].upper()}: {msg['content']}\n"

    prompt = f"""
    Continue the coaching conversation.
    
    HISTORY:
    {chat_history_text}
    
    USER: {request.message}
    
    AI COACH:
    """

    try:
        result = await ai_router.route(
            prompt=prompt,
            system_message=system_msg,
            max_tokens=300,
            temperature=0.7
        )
        
        ai_reply = result["content"]
        
        # Append AI response
        session.messages.append({"role": "assistant", "content": ai_reply})
        flag_modified(session, "messages")
        session.updated_at = datetime.utcnow()
        db.commit()

        return {
            "session_id": session.id,
            "message": ai_reply,
            "role": "assistant"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
