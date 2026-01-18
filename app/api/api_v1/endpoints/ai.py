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

@router.post("/socratic")
def socratic_tutor(
    request: ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Socratic Tutor: Asks guiding questions instead of giving answers.
    """
    system_prompt = f"""You are a Socratic Tutor in the Vedic 'Guru-Shishya' tradition. 
The student's name is {current_user.full_name or current_user.email}.

Your Goal: Help the student derive the answer themselves.
Rules:
1. NEVER give the direct answer.
2. Ask leading questions based on the student's input.
3. If they are completely stuck, give a hint, but still ask a question.
4. Keep responses short (max 2-3 sentences).
5. Be encouraging but firm in the methodology.

Context: {request.context or 'General Study'}
"""

    messages = [{"role": "user", "content": request.message}]

    try:
        response = gemini_service.chat(
            messages=messages, 
            user=current_user,
            system_prompt=system_prompt, 
            temperature=0.7
        )
        return {"response": response}
    except Exception as e:
        print(f"Socratic Error: {e}")
        return {"response": "I'm contemplating... please try asking again."}

@router.post("/mindmap")
def generate_mindmap(
    request: ChatRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Generates a generic mind map structure for a given topic.
    Returns JSON { nodes: [], edges: [] } suited for ReactFlow.
    """
    topic = request.message # Reusing message field as topic input
    
    prompt = f"""Generate a detailed concept map for the topic: "{topic}".
Focus on key sub-concepts, relationships, and hierarchy.

Return JSON ONLY in this format:
{{
    "nodes": [
        {{ "id": "1", "label": "{topic} (Root)", "type": "input", "position": {{ "x": 0, "y": 0 }} }},
        {{ "id": "2", "label": "Subconcept A", "type": "default", "position": {{ "x": 100, "y": 100 }} }}
    ],
    "edges": [
        {{ "id": "e1-2", "source": "1", "target": "2", "label": "includes" }}
    ]
}}
Ensure unique IDs. Max 15 nodes. Provide rough x/y positions (spread out) if possible, but frontend will handle layout.
"""
    try:
        response_text = gemini_service.generate_text(prompt, user=current_user, temperature=0.3, is_complex=True)
        # Parse JSON
        import json
        clean = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        return data
    except Exception as e:
        print(f"MindMap Error: {e}")
        return {"nodes": [], "edges": [], "error": str(e)}
