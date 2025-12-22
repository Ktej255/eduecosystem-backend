from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.services.ai_service import ai_service
from app.schemas import ai_tutor as schemas
from app.crud import ai_conversation as crud_conversation

router = APIRouter()


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat_with_tutor(
    request: schemas.ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Chat with the AI tutor.
    Creates a new conversation if conversation_id is not provided.
    """
    if request.conversation_id:
        conversation = crud_conversation.ai_conversation.get(
            db, id=request.conversation_id
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        # Create new conversation
        conversation_in = schemas.AIConversationCreate(
            initial_message=request.message,
            context=request.context,
            title=f"Chat about {request.context}" if request.context else "New Chat",
        )
        conversation = crud_conversation.ai_conversation.create_with_user(
            db, obj_in=conversation_in, user_id=current_user.id
        )

    # Get history
    history = conversation.messages if conversation.messages else []

    # Get AI response
    try:
        response_text = await ai_service.chat_with_tutor(
            message=request.message,
            history=history,
            context=request.context or conversation.context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Update conversation with new messages
    # Add user message if it wasn't the initial one (initial one is added in create_with_user)
    if request.conversation_id:
        crud_conversation.ai_conversation.add_message(
            db, conversation_id=conversation.id, role="user", content=request.message
        )

    # Add assistant response
    updated_conversation = crud_conversation.ai_conversation.add_message(
        db, conversation_id=conversation.id, role="assistant", content=response_text
    )

    return {
        "response": response_text,
        "conversation_id": updated_conversation.id,
        "history": updated_conversation.messages,
    }


@router.get("/history", response_model=List[schemas.AIConversation])
def get_conversation_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get conversation history for the current user.
    """
    return crud_conversation.ai_conversation.get_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.post("/explain", response_model=Dict)
async def explain_concept(
    request: schemas.ExplainRequest, current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get a detailed explanation of a concept.
    """
    try:
        return await ai_service.explain_concept(
            concept=request.concept, level=request.level, context=request.context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/practice", response_model=List[Dict])
async def generate_practice(
    request: schemas.PracticeRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Generate practice problems.
    """
    try:
        return await ai_service.generate_practice_problems(
            topic=request.topic, difficulty=request.difficulty, count=request.count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review", response_model=Dict)
async def review_code(
    request: schemas.CodeReviewRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Review code and provide feedback.
    """
    try:
        return await ai_service.review_code(
            code=request.code, language=request.language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan", response_model=Dict)
async def create_study_plan(
    request: schemas.StudyPlanRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a personalized study plan.
    """
    try:
        return await ai_service.create_study_plan(
            goal=request.goal,
            duration=request.duration,
            hours_per_week=request.hours_per_week,
            current_knowledge=request.current_knowledge,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
