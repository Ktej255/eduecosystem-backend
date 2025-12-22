"""
Chatbot Service
Handles conversation logic, context management, and AI integration
"""

from sqlalchemy.orm import Session
from typing import List, Dict
from app.services.ai_service import ai_service
from app.crud import chatbot as crud_chatbot
from app.schemas.chatbot import ChatMessageCreate, ChatRequest, ChatResponse
from app.models.user import User
from app.models.course import Course
from app.models.lesson import Lesson


class ChatbotService:
    """Service for managing chatbot conversations"""

    def __init__(self):
        self.max_context_messages = 10

    async def send_message(
        self, db: Session, request: ChatRequest, user: User
    ) -> ChatResponse:
        """
        Process user message and generate AI response

        Args:
            db: Database session
            request: Chat request with message and context
            user: Current user

        Returns:
            ChatResponse with bot reply
        """
        # Get or create session
        if request.session_id:
            session = crud_chatbot.get_chat_session(db, request.session_id)
            if not session or session.user_id != user.id:
                raise ValueError("Invalid session")
        else:
            from app.schemas.chatbot import ChatSessionCreate

            session = crud_chatbot.create_chat_session(
                db,
                ChatSessionCreate(
                    course_id=request.course_id,
                    context_type=request.context_type or "general",
                    context_id=request.context_id,
                ),
                user.id,
            )

        # Save user message
        user_message = crud_chatbot.create_chat_message(
            db,
            ChatMessageCreate(
                session_id=session.id, role="user", content=request.message
            ),
        )

        # Build context
        context = await self._build_context(db, session, user)

        # Get conversation history
        recent_messages = crud_chatbot.get_recent_messages(
            db, session.id, self.max_context_messages
        )

        # Generate AI response
        system_message = self._create_system_message(context)
        conversation_history = self._format_conversation_history(recent_messages)

        ai_response = await ai_service.generate_text(
            prompt=f"{conversation_history}\n\nUser: {request.message}\n\nAssistant:",
            system_message=system_message,
            max_tokens=800,
        )

        # Save assistant response
        assistant_message = crud_chatbot.create_chat_message(
            db,
            ChatMessageCreate(
                session_id=session.id,
                role="assistant",
                content=ai_response,
                metadata={"context": context},
            ),
        )

        # Generate suggested follow-up questions
        suggestions = await self._generate_suggestions(
            request.message, ai_response, context
        )

        return ChatResponse(
            session_id=session.id,
            message=user_message,
            response=assistant_message,
            suggestions=suggestions,
        )

    async def _build_context(self, db: Session, session, user: User) -> Dict:
        """Build context information for AI"""
        context = {
            "user_name": user.full_name or user.username,
            "context_type": session.context_type,
        }

        # Add course context
        if session.course_id:
            course = db.query(Course).filter(Course.id == session.course_id).first()
            if course:
                context["course_title"] = course.title
                context["course_description"] = course.description

        # Add lesson context if applicable
        if session.context_type == "lesson" and session.context_id:
            lesson = db.query(Lesson).filter(Lesson.id == session.context_id).first()
            if lesson:
                context["lesson_title"] = lesson.title
                context["lesson_content_summary"] = (
                    lesson.content[:500] if lesson.content else ""
                )

        return context

    def _create_system_message(self, context: Dict) -> str:
        """Create system message for AI with context"""
        base_message = """You are a helpful AI learning assistant for an online education platform.
Your role is to help students with their coursework, answer questions about course content,
provide study tips, and offer encouragement.

Guidelines:
- Be friendly, patient, and encouraging
- Provide clear, accurate explanations
- Break down complex topics into simpler parts
- Suggest relevant course resources when applicable
- If you don't know something, admit it and suggest asking the instructor
- Keep responses concise but informative (2-3 paragraphs max)
"""

        # Add context-specific information
        if "course_title" in context:
            base_message += f"\n\nCurrent Course: {context['course_title']}"

        if "lesson_title" in context:
            base_message += f"\nCurrent Lesson: {context['lesson_title']}"

        if "user_name" in context:
            base_message += f"\nStudent Name: {context['user_name']}"

        return base_message

    def _format_conversation_history(self, messages: List) -> str:
        """Format recent messages for context"""
        formatted = []
        for msg in messages[-5:]:  # Last 5 messages for context
            role = "User" if msg.role == "user" else "Assistant"
            formatted.append(f"{role}: {msg.content}")
        return "\n\n".join(formatted)

    async def _generate_suggestions(
        self, user_message: str, ai_response: str, context: Dict
    ) -> List[str]:
        """Generate follow-up question suggestions"""
        try:
            prompt = f"""Based on this conversation, suggest 2-3 brief follow-up questions the student might ask.
            
User question: {user_message}
AI response: {ai_response}

Return only a JSON array of question strings, e.g. ["Question 1?", "Question 2?"]"""

            response = await ai_service.generate_text(
                prompt=prompt, max_tokens=150, temperature=0.7
            )

            import json

            suggestions = json.loads(response)
            return suggestions[:3]  # Max 3 suggestions
        except:
            # Fallback suggestions
            return [
                "Can you explain that in more detail?",
                f"How does this relate to {context.get('course_title', 'the course')}?",
                "Do you have any examples?",
            ]


chatbot_service = ChatbotService()
