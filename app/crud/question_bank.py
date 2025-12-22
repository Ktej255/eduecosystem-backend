from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
import random
import json

from app.crud.base import CRUDBase
from app.models.question_bank import (
    QuestionBank,
    BankQuestion,
    QuizQuestionPool,
    question_bank_questions,
)
from app.models.quiz import Question, QuestionOption
from app.schemas.question_bank import (
    QuestionBankCreate,
    QuestionBankUpdate,
    BankQuestionCreate,
    BankQuestionUpdate,
    QuizQuestionPoolCreate,
)


class CRUDQuestionBank(CRUDBase[QuestionBank, QuestionBankCreate, QuestionBankUpdate]):
    def get_by_course(
        self,
        db: Session,
        *,
        course_id: int,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> List[QuestionBank]:
        """Get question banks for a course"""
        query = db.query(QuestionBank).filter(QuestionBank.course_id == course_id)

        if not include_inactive:
            query = query.filter(QuestionBank.is_active == True)

        return (
            query.order_by(desc(QuestionBank.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_instructor(
        self, db: Session, *, obj_in: QuestionBankCreate, instructor_id: int
    ) -> QuestionBank:
        """Create a question bank"""
        db_obj = QuestionBank(**obj_in.model_dump(), instructor_id=instructor_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CRUDBankQuestion:
    def get_by_bank(
        self,
        db: Session,
        *,
        bank_id: int,
        difficulty: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BankQuestion]:
        """Get questions from a question bank"""
        query = (
            db.query(BankQuestion)
            .join(question_bank_questions)
            .filter(question_bank_questions.c.question_bank_id == bank_id)
        )

        if difficulty:
            query = query.filter(BankQuestion.difficulty == difficulty)

        return query.offset(skip).limit(limit).all()

    def get_by_instructor(
        self, db: Session, *, instructor_id: int, skip: int = 0, limit: int = 100
    ) -> List[BankQuestion]:
        """Get all questions created by instructor"""
        return (
            db.query(BankQuestion)
            .filter(BankQuestion.instructor_id == instructor_id)
            .order_by(desc(BankQuestion.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_instructor(
        self, db: Session, *, obj_in: BankQuestionCreate, instructor_id: int
    ) -> BankQuestion:
        """Create a bank question and add to banks"""
        obj_data = obj_in.dict(exclude={"question_bank_ids"})
        db_obj = BankQuestion(**obj_data, instructor_id=instructor_id)
        db.add(db_obj)
        db.flush()

        # Add to question banks
        if obj_in.question_bank_ids:
            for bank_id in obj_in.question_bank_ids:
                bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()
                if bank:
                    bank.questions.append(db_obj)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, question_id: int, obj_in: BankQuestionUpdate
    ) -> Optional[BankQuestion]:
        """Update a bank question"""
        question = db.query(BankQuestion).filter(BankQuestion.id == question_id).first()
        if not question:
            return None

        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)

        db.commit()
        db.refresh(question)
        return question

    def delete(self, db: Session, *, question_id: int) -> bool:
        """Delete a bank question"""
        question = db.query(BankQuestion).filter(BankQuestion.id == question_id).first()
        if not question:
            return False

        db.delete(question)
        db.commit()
        return True

    def add_to_bank(self, db: Session, *, question_id: int, bank_id: int) -> bool:
        """Add question to a question bank"""
        question = db.query(BankQuestion).filter(BankQuestion.id == question_id).first()
        bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()

        if not question or not bank:
            return False

        if question not in bank.questions:
            bank.questions.append(question)
            db.commit()

        return True

    def remove_from_bank(self, db: Session, *, question_id: int, bank_id: int) -> bool:
        """Remove question from a question bank"""
        question = db.query(BankQuestion).filter(BankQuestion.id == question_id).first()
        bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()

        if not question or not bank:
            return False

        if question in bank.questions:
            bank.questions.remove(question)
            db.commit()

        return True


class CRUDQuizGeneration:
    def generate_quiz_from_pools(
        self, db: Session, *, quiz_id: int, pools: List[QuizQuestionPoolCreate]
    ) -> dict:
        """Generate quiz questions from question bank pools"""
        from app.models.quiz import Quiz

        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return {"error": "Quiz not found"}

        total_added = 0
        questions_by_pool = {}

        for pool in pools:
            # Get questions from bank
            query = (
                db.query(BankQuestion)
                .join(question_bank_questions)
                .filter(
                    question_bank_questions.c.question_bank_id == pool.question_bank_id
                )
            )

            if pool.difficulty_filter:
                query = query.filter(BankQuestion.difficulty == pool.difficulty_filter)

            available_questions = query.all()

            # Randomly select questions
            num_to_select = min(pool.num_questions, len(available_questions))
            selected_questions = random.sample(available_questions, num_to_select)

            # Add to quiz
            for idx, bank_q in enumerate(selected_questions):
                quiz_question = Question(
                    quiz_id=quiz_id,
                    text=bank_q.text,
                    type=bank_q.type,
                    points=bank_q.points,
                    explanation=bank_q.explanation,
                    order_index=total_added + idx,
                )

                # Copy options if exists
                # Copy options if exists
                if bank_q.options:
                    try:
                        options_list = json.loads(bank_q.options)
                        if isinstance(options_list, list):
                            for opt_idx, opt_text in enumerate(options_list):
                                is_correct = opt_text == bank_q.correct_answer
                                option = QuestionOption(
                                    text=str(opt_text),
                                    is_correct=is_correct,
                                    order_index=opt_idx,
                                )
                                quiz_question.options.append(option)
                    except json.JSONDecodeError:
                        pass

                db.add(quiz_question)
                bank_q.usage_count += 1

            questions_by_pool[pool.question_bank_id] = num_to_select
            total_added += num_to_select

            # Save pool configuration
            pool_config = QuizQuestionPool(
                quiz_id=quiz_id,
                question_bank_id=pool.question_bank_id,
                num_questions=pool.num_questions,
                difficulty_filter=pool.difficulty_filter,
            )
            db.add(pool_config)

        db.commit()

        return {
            "quiz_id": quiz_id,
            "total_questions_added": total_added,
            "questions_by_pool": questions_by_pool,
            "message": f"Successfully added {total_added} questions to quiz",
        }


# Create instances
question_bank = CRUDQuestionBank(QuestionBank)
bank_question = CRUDBankQuestion()
quiz_generation = CRUDQuizGeneration()
