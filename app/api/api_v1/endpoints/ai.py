from typing import Any, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.services.gemini_service import gemini_service
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None  # Optional context about user's learning journey


@router.post("/chat")
def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Chat with the Global AI Assistant powered by Gemini.
    Provides personalized learning guidance and support.
    """

    # Build context-aware system prompt
    system_prompt = f"""You are a helpful AI learning assistant for the Holistic Learning Ecosystem platform.
The student's name is {current_user.full_name or current_user.email}.

Your role is to:
1. Provide personalized learning guidance and study recommendations
2. Help students stay focused and motivated
3. Answer questions about courses, wellness, and study techniques
4. Analyze their learning patterns and suggest improvements
5. Be encouraging, supportive, and empathetic

Keep responses concise (2-3 sentences) and actionable.
"""

    # Add any additional context provided
    if request.context:
        system_prompt += f"\n\nCurrent context: {request.context}"

    # Prepare conversation messages
    messages = [{"role": "user", "content": request.message}]

    try:
        # Get AI response from Gemini
        response = gemini_service.chat(
            messages=messages, 
            user=current_user,
            system_prompt=system_prompt, 
            temperature=0.7
        )

        return {"response": response}

    except Exception as e:
        print(f"Gemini Chat Error: {e}")
        # Fallback response if Gemini fails
        return {
            "response": "I'm here to help you with your learning journey! However, I'm having trouble connecting right now. Please try asking your question again, or check with support if this persists."
        }
