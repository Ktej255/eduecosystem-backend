from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.live_class_interactive import (
    LiveClassPoll,
    LiveClassPollResponse,
    LiveClassQuestion,
    LiveClassReaction,
    LiveClassChatMessage,
    PollStatus,
)
from app.schemas.live_class_interactive import (
    PollCreate,
    PollResponseCreate,
    QuestionCreate,
    QuestionAnswer,
    ChatMessageCreate,
    ReactionCreate,
)


class CRUDLiveClassInteractive:
    # Polls
    def create_poll(
        self, db: Session, *, obj_in: PollCreate, live_class_id: int
    ) -> LiveClassPoll:
        db_obj = LiveClassPoll(
            live_class_id=live_class_id,
            question=obj_in.question,
            options=obj_in.options,
            correct_option_index=obj_in.correct_option_index,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_polls(self, db: Session, *, live_class_id: int) -> List[LiveClassPoll]:
        return (
            db.query(LiveClassPoll)
            .filter(LiveClassPoll.live_class_id == live_class_id)
            .all()
        )

    def get_poll(self, db: Session, *, poll_id: int) -> Optional[LiveClassPoll]:
        return db.query(LiveClassPoll).filter(LiveClassPoll.id == poll_id).first()

    def update_poll_status(
        self, db: Session, *, poll_id: int, status: PollStatus
    ) -> Optional[LiveClassPoll]:
        poll = self.get_poll(db, poll_id=poll_id)
        if poll:
            poll.status = status
            if status == PollStatus.ENDED:
                from datetime import datetime

                poll.ended_at = datetime.utcnow()
            db.commit()
            db.refresh(poll)
        return poll

    def create_poll_response(
        self, db: Session, *, obj_in: PollResponseCreate, student_id: int
    ) -> LiveClassPollResponse:
        db_obj = LiveClassPollResponse(
            poll_id=obj_in.poll_id,
            student_id=student_id,
            selected_option_index=obj_in.selected_option_index,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_poll_responses(
        self, db: Session, *, poll_id: int
    ) -> List[LiveClassPollResponse]:
        return (
            db.query(LiveClassPollResponse)
            .filter(LiveClassPollResponse.poll_id == poll_id)
            .all()
        )

    # Questions (Q&A)
    def create_question(
        self,
        db: Session,
        *,
        obj_in: QuestionCreate,
        live_class_id: int,
        student_id: int,
    ) -> LiveClassQuestion:
        db_obj = LiveClassQuestion(
            live_class_id=live_class_id,
            student_id=student_id,
            question_text=obj_in.question_text,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_questions(
        self, db: Session, *, live_class_id: int
    ) -> List[LiveClassQuestion]:
        return (
            db.query(LiveClassQuestion)
            .filter(LiveClassQuestion.live_class_id == live_class_id)
            .order_by(LiveClassQuestion.created_at.desc())
            .all()
        )

    def answer_question(
        self, db: Session, *, question_id: int, obj_in: QuestionAnswer
    ) -> Optional[LiveClassQuestion]:
        question = (
            db.query(LiveClassQuestion)
            .filter(LiveClassQuestion.id == question_id)
            .first()
        )
        if question:
            question.answer_text = obj_in.answer_text
            question.is_answered = True
            from datetime import datetime

            question.answered_at = datetime.utcnow()
            db.commit()
            db.refresh(question)
        return question

    def upvote_question(
        self, db: Session, *, question_id: int
    ) -> Optional[LiveClassQuestion]:
        question = (
            db.query(LiveClassQuestion)
            .filter(LiveClassQuestion.id == question_id)
            .first()
        )
        if question:
            question.upvotes += 1
            db.commit()
            db.refresh(question)
        return question

    # Chat
    def create_chat_message(
        self,
        db: Session,
        *,
        obj_in: ChatMessageCreate,
        live_class_id: int,
        user_id: int,
        is_instructor: bool = False,
    ) -> LiveClassChatMessage:
        db_obj = LiveClassChatMessage(
            live_class_id=live_class_id,
            user_id=user_id,
            message=obj_in.message,
            is_instructor=is_instructor,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_chat_messages(
        self, db: Session, *, live_class_id: int, limit: int = 100
    ) -> List[LiveClassChatMessage]:
        return (
            db.query(LiveClassChatMessage)
            .filter(LiveClassChatMessage.live_class_id == live_class_id)
            .order_by(LiveClassChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )

    # Reactions
    def create_reaction(
        self,
        db: Session,
        *,
        obj_in: ReactionCreate,
        live_class_id: int,
        student_id: int,
    ) -> LiveClassReaction:
        db_obj = LiveClassReaction(
            live_class_id=live_class_id,
            student_id=student_id,
            reaction_type=obj_in.reaction_type,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


live_class_interactive = CRUDLiveClassInteractive()
