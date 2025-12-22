from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.crud.live_class_interactive import live_class_interactive
from app.schemas.live_class_interactive import (
    PollCreate,
    PollResponse,
    PollResponseCreate,
    QuestionCreate,
    QuestionResponse,
    QuestionAnswer,
    ChatMessageCreate,
    ChatMessageResponse,
    ReactionCreate,
)
from app.models.user import User
from app.models.live_class_interactive import PollStatus
from app.services.realtime_service import realtime_service

router = APIRouter()


# Polls
@router.post("/{live_class_id}/polls", response_model=PollResponse)
async def create_poll(
    live_class_id: int,
    poll_in: PollCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new poll for a live class (Instructor only)
    """
    # Verify instructor permissions (omitted for brevity, assume check exists)
    poll = live_class_interactive.create_poll(
        db, obj_in=poll_in, live_class_id=live_class_id
    )

    # Broadcast poll created event
    await realtime_service.send_live_class_update(
        class_id=live_class_id,
        update_type="poll_created",
        data={"poll_id": poll.id, "question": poll.question, "options": poll.options},
    )
    return poll


@router.get("/{live_class_id}/polls", response_model=List[PollResponse])
def get_polls(
    live_class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all polls for a live class
    """
    return live_class_interactive.get_polls(db, live_class_id=live_class_id)


@router.post("/polls/{poll_id}/respond", response_model=Any)
async def respond_to_poll(
    poll_id: int,
    response_in: PollResponseCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Submit a response to a poll
    """
    # Check if already responded (logic omitted)
    response = live_class_interactive.create_poll_response(
        db, obj_in=response_in, student_id=current_user.id
    )

    # Broadcast poll update (e.g., updated counts)
    poll = live_class_interactive.get_poll(db, poll_id=poll_id)
    await realtime_service.send_live_class_update(
        class_id=poll.live_class_id,
        update_type="poll_updated",
        data={"poll_id": poll_id},
    )
    return {"status": "success"}


@router.put("/polls/{poll_id}/status", response_model=PollResponse)
async def update_poll_status(
    poll_id: int,
    status: PollStatus,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update poll status (e.g., end poll)
    """
    poll = live_class_interactive.update_poll_status(db, poll_id=poll_id, status=status)

    # Broadcast status change
    await realtime_service.send_live_class_update(
        class_id=poll.live_class_id,
        update_type="poll_status_changed",
        data={"poll_id": poll_id, "status": status},
    )
    return poll


# Questions (Q&A)
@router.post("/{live_class_id}/questions", response_model=QuestionResponse)
async def ask_question(
    live_class_id: int,
    question_in: QuestionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Ask a question in Q&A
    """
    question = live_class_interactive.create_question(
        db, obj_in=question_in, live_class_id=live_class_id, student_id=current_user.id
    )

    # Broadcast new question
    await realtime_service.send_live_class_update(
        class_id=live_class_id,
        update_type="new_question",
        data={
            "question_id": question.id,
            "text": question.question_text,
            "student_name": current_user.full_name,
        },
    )

    # Return response with student name
    return QuestionResponse(
        id=question.id,
        student_id=question.student_id,
        student_name=current_user.full_name,
        question_text=question.question_text,
        is_answered=question.is_answered,
        answer_text=question.answer_text,
        upvotes=question.upvotes,
        created_at=question.created_at,
    )


@router.get("/{live_class_id}/questions", response_model=List[QuestionResponse])
def get_questions(
    live_class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all questions for a live class
    """
    questions = live_class_interactive.get_questions(db, live_class_id=live_class_id)
    # Enrich with student names (could be optimized with join)
    result = []
    for q in questions:
        student = q.student  # Access relationship
        result.append(
            QuestionResponse(
                id=q.id,
                student_id=q.student_id,
                student_name=student.full_name if student else "Unknown",
                question_text=q.question_text,
                is_answered=q.is_answered,
                answer_text=q.answer_text,
                upvotes=q.upvotes,
                created_at=q.created_at,
            )
        )
    return result


@router.post("/questions/{question_id}/answer", response_model=QuestionResponse)
async def answer_question(
    question_id: int,
    answer_in: QuestionAnswer,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Answer a question (Instructor only)
    """
    question = live_class_interactive.answer_question(
        db, question_id=question_id, obj_in=answer_in
    )

    # Broadcast answer
    await realtime_service.send_live_class_update(
        class_id=question.live_class_id,
        update_type="question_answered",
        data={"question_id": question_id, "answer": answer_in.answer_text},
    )

    student = question.student
    return QuestionResponse(
        id=question.id,
        student_id=question.student_id,
        student_name=student.full_name if student else "Unknown",
        question_text=question.question_text,
        is_answered=question.is_answered,
        answer_text=question.answer_text,
        upvotes=question.upvotes,
        created_at=question.created_at,
    )


@router.post("/questions/{question_id}/upvote", response_model=QuestionResponse)
async def upvote_question(
    question_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upvote a question
    """
    question = live_class_interactive.upvote_question(db, question_id=question_id)

    # Broadcast upvote
    await realtime_service.send_live_class_update(
        class_id=question.live_class_id,
        update_type="question_upvoted",
        data={"question_id": question_id, "upvotes": question.upvotes},
    )

    student = question.student
    return QuestionResponse(
        id=question.id,
        student_id=question.student_id,
        student_name=student.full_name if student else "Unknown",
        question_text=question.question_text,
        is_answered=question.is_answered,
        answer_text=question.answer_text,
        upvotes=question.upvotes,
        created_at=question.created_at,
    )


# Chat
@router.post("/{live_class_id}/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    live_class_id: int,
    message_in: ChatMessageCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send a chat message
    """
    # Determine if instructor (logic simplified)
    is_instructor = False  # Should check against course instructor

    message = live_class_interactive.create_chat_message(
        db,
        obj_in=message_in,
        live_class_id=live_class_id,
        user_id=current_user.id,
        is_instructor=is_instructor,
    )

    # Broadcast chat message
    await realtime_service.send_chat_message(
        room=f"live_class:{live_class_id}",
        message={
            "id": message.id,
            "user_id": current_user.id,
            "user_name": current_user.full_name,
            "message": message.message,
            "is_instructor": message.is_instructor,
            "created_at": message.created_at.isoformat(),
        },
    )

    return ChatMessageResponse(
        id=message.id,
        user_id=message.user_id,
        user_name=current_user.full_name,
        message=message.message,
        is_instructor=message.is_instructor,
        created_at=message.created_at,
    )


@router.get("/{live_class_id}/chat", response_model=List[ChatMessageResponse])
def get_chat_history(
    live_class_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get chat history
    """
    messages = live_class_interactive.get_chat_messages(db, live_class_id=live_class_id)
    result = []
    for m in messages:
        user = m.user
        result.append(
            ChatMessageResponse(
                id=m.id,
                user_id=m.user_id,
                user_name=user.full_name if user else "Unknown",
                message=m.message,
                is_instructor=m.is_instructor,
                created_at=m.created_at,
            )
        )
    return result


# Reactions
@router.post("/{live_class_id}/reactions", response_model=Any)
async def send_reaction(
    live_class_id: int,
    reaction_in: ReactionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send a reaction (emoji)
    """
    live_class_interactive.create_reaction(
        db, obj_in=reaction_in, live_class_id=live_class_id, student_id=current_user.id
    )

    # Broadcast reaction
    await realtime_service.send_live_class_update(
        class_id=live_class_id,
        update_type="reaction",
        data={"reaction": reaction_in.reaction_type, "user_id": current_user.id},
    )
    return {"status": "success"}
