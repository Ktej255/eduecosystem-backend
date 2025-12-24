"""
Chatbot Service (Fresh 2025)
Handles pedagogical conversation using Tiered Gemini AI.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.services.gemini_service import gemini_service
from app.crud import chatbot as crud_chatbot
from app.schemas.chatbot import ChatMessageCreate, ChatRequest, ChatResponse
from app.models.user import User

class ChatbotService:
    async def send_message(self, db: Session, request: ChatRequest, user: User) -> ChatResponse:
        # Save user message
        crud_chatbot.create_chat_message(db, ChatMessageCreate(session_id=request.session_id, role="user", content=request.message))
        
        # Build prompt from history...
        # Delegate to gemini_service (Chat is Gemini 3 Flash by default, Pro for Premium)
        ai_response = gemini_service.chat(
            messages=[{"role": "user", "content": request.message}],
            user=user
        )
        
        # Save assistant response
        assistant_message = crud_chatbot.create_chat_message(db, ChatMessageCreate(session_id=request.session_id, role="assistant", content=ai_response))
        
        return ChatResponse(session_id=request.session_id, response=assistant_message)

chatbot_service = ChatbotService()
