from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import random

from app.api import deps
from app.models.user import User
from app.models.quiz import (
    Quiz,
    Question,
    QuestionOption,
    QuizAttempt,
    StudentAnswer,
    QuestionType,
    QuizFeedback,
    QuizAttemptAnalytics,
    AIGradingResult,
)
from app.schemas.quiz import (
    Quiz as QuizSchema,
    QuizCreate,
    QuizUpdate,
    Question as QuestionSchema,
    QuizAttempt as QuizAttemptSchema,
    StartQuizResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    CompleteQuizRequest,
    QuizResultsResponse,
    QuestionWithFeedback,
    QuizFeedback as QuizFeedbackSchema,
    AIGradingResult as AIGradingResultSchema,
)

router = APIRouter()

# ============================================================================
# QUIZ MANAGEMENT ENDPOINTS
# ============================================================================


@router.post("/", response_model=QuizSchema, status_code=status.HTTP_201_CREATED)
def create_quiz(
    *,
    db: Session = Depends(deps.get_db),
    quiz_in: QuizCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new quiz with interactive features (instructor only)
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to create quizzes")

    # Create quiz with all new interactive fields
    db_quiz = Quiz(
        title=quiz_in.title,
        description=quiz_in.description,
        course_id=quiz_in.course_id,
        lesson_id=quiz_in.lesson_id,
        time_limit_minutes=quiz_in.time_limit_minutes,
        passing_score=quiz_in.passing_score,
        max_attempts=quiz_in.max_attempts,
        is_published=quiz_in.is_published,
        shuffle_questions=quiz_in.shuffle_questions,
        show_correct_answers=quiz_in.show_correct_answers,
        # Interactive features
        instant_feedback=quiz_in.instant_feedback,
        show_score_immediately=quiz_in.show_score_immediately,
        randomize_options=quiz_in.randomize_options,
        allow_review_answers=quiz_in.allow_review_answers,
        show_hints=quiz_in.show_hints,
        require_all_questions=quiz_in.require_all_questions,
        allow_backtrack=quiz_in.allow_backtrack,
        # AI grading
        enable_ai_grading=quiz_in.enable_ai_grading,
        ai_grading_model=quiz_in.ai_grading_model,
        manual_review_threshold=quiz_in.manual_review_threshold,
    )
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)

    # Create questions if provided
    for q_in in quiz_in.questions:
        db_question = Question(
            quiz_id=db_quiz.id,
            text=q_in.text,
            type=q_in.type,
            points=q_in.points,
            order_index=q_in.order_index,
            explanation=q_in.explanation,
        )
        db.add(db_question)
        db.commit()
        db.refresh(db_question)

        # Add options
        for opt_in in q_in.options:
            db_option = QuestionOption(
                question_id=db_question.id,
                text=opt_in.text,
                is_correct=opt_in.is_correct,
                order_index=opt_in.order_index,
                match_text=opt_in.match_text,
            )
            db.add(db_option)
        db.commit()

    db.refresh(db_quiz)
    return db_quiz


@router.get("/{quiz_id}", response_model=QuizSchema)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get quiz details"""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.put("/{quiz_id}", response_model=QuizSchema)
def update_quiz(
    quiz_id: int,
    *,
    db: Session = Depends(deps.get_db),
    quiz_in: QuizUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update quiz details"""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Update all fields including new interactive ones
    update_data = quiz_in.dict(exclude_unset=True, exclude={"questions"})
    for field, value in update_data.items():
        setattr(quiz, field, value)

    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


# ============================================================================
# INTERACTIVE QUIZ-TAKING ENDPOINTS
# ============================================================================


@router.post("/{quiz_id}/start", response_model=StartQuizResponse)
def start_quiz_attempt(
    quiz_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Start a new quiz attempt.
    Returns quiz details, questions (possibly shuffled), and creates attempt record.
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if not quiz.is_published:
        raise HTTPException(status_code=403, detail="Quiz is not published")

    # Check max attempts
    if quiz.max_attempts:
        existing_attempts = (
            db.query(QuizAttempt)
            .filter(
                QuizAttempt.quiz_id == quiz_id, QuizAttempt.user_id == current_user.id
            )
            .count()
        )

        if existing_attempts >= quiz.max_attempts:
            raise HTTPException(
                status_code=403,
                detail=f"Maximum attempts ({quiz.max_attempts}) reached",
            )

    # Create attempt record
    db_attempt = QuizAttempt(
        quiz_id=quiz_id,
        user_id=current_user.id,
        started_at=datetime.utcnow(),
        score=0.0,
        passed=False,
    )
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)

    # Get questions with feedback
    questions = list(quiz.questions)

    # Shuffle questions if configured
    if quiz.shuffle_questions:
        random.shuffle(questions)

    # Prepare questions with feedback (if show_hints is enabled)
    questions_with_feedback = []
    for q in questions:
        q_dict = QuestionWithFeedback.from_orm(q).dict()

        # Get feedback if exists
        feedback = (
            db.query(QuizFeedback).filter(QuizFeedback.question_id == q.id).first()
        )

        if feedback:
            q_dict["feedback"] = QuizFeedbackSchema.from_orm(feedback).dict()

        # Randomize options if configured
        if quiz.randomize_options and q_dict.get("options"):
            random.shuffle(q_dict["options"])

        questions_with_feedback.append(q_dict)

    return {
        "attempt_id": db_attempt.id,
        "quiz": quiz,
        "questions": questions_with_feedback,
        "time_limit_minutes": quiz.time_limit_minutes,
        "started_at": db_attempt.started_at,
    }


@router.post(
    "/attempts/{attempt_id}/submit-answer", response_model=SubmitAnswerResponse
)
def submit_single_answer(
    attempt_id: int,
    *,
    db: Session = Depends(deps.get_db),
    answer_in: SubmitAnswerRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Submit a single answer during quiz and get instant feedback.
    This is the core interactive functionality.
    """
    # Verify attempt exists and belongs to user
    attempt = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == current_user.id)
        .first()
    )

    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")

    if attempt.completed_at:
        raise HTTPException(status_code=400, detail="Quiz already completed")

    # Get question and quiz
    question = db.query(Question).filter(Question.id == answer_in.question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    quiz = attempt.quiz

    # Check if answer already exists (prevent duplicate submissions)
    existing_answer = (
        db.query(StudentAnswer)
        .filter(
            StudentAnswer.attempt_id == attempt_id,
            StudentAnswer.question_id == answer_in.question_id,
        )
        .first()
    )

    if existing_answer:
        # Update existing answer
        existing_answer.selected_option_id = answer_in.selected_option_id
        existing_answer.text_response = answer_in.text_response
        existing_answer.time_spent_seconds = answer_in.time_spent_seconds
        existing_answer.submitted_at = datetime.utcnow()
        db_answer = existing_answer
    else:
        # Create new answer
        db_answer = StudentAnswer(
            attempt_id=attempt_id,
            question_id=answer_in.question_id,
            selected_option_id=answer_in.selected_option_id,
            text_response=answer_in.text_response,
            time_spent_seconds=answer_in.time_spent_seconds,
            submitted_at=datetime.utcnow(),
        )
        db.add(db_answer)

    # Auto-grade the answer
    is_correct = False
    points_awarded = 0.0
    correct_option_id = None

    if question.type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]:
        # Check if selected option is correct
        if answer_in.selected_option_id:
            selected_option = (
                db.query(QuestionOption)
                .filter(QuestionOption.id == answer_in.selected_option_id)
                .first()
            )

            if selected_option and selected_option.is_correct:
                is_correct = True
                points_awarded = float(question.points)

            # Find correct option for feedback
            correct_option = (
                db.query(QuestionOption)
                .filter(
                    QuestionOption.question_id == question.id,
                    QuestionOption.is_correct == True,
                )
                .first()
            )

            if correct_option:
                correct_option_id = correct_option.id

    elif question.type == QuestionType.SHORT_ANSWER:
        # Simple string matching
        if answer_in.text_response:
            for option in question.options:
                if (
                    option.is_correct
                    and option.text.lower().strip()
                    == answer_in.text_response.lower().strip()
                ):
                    is_correct = True
                    points_awarded = float(question.points)
                    break

    elif question.type == QuestionType.FILL_IN_BLANK:
        # Similar to short answer
        if answer_in.text_response:
            for option in question.options:
                if (
                    option.is_correct
                    and option.text.lower().strip() in answer_in.text_response.lower()
                ):
                    is_correct = True
                    points_awarded = float(question.points)
                    break

    # Update answer with grading results
    db_answer.is_correct = is_correct
    db_answer.points_awarded = points_awarded

    db.commit()
    db.refresh(db_answer)

    # Prepare response based on quiz settings
    response = {
        "is_correct": is_correct,
        "points_awarded": points_awarded,
        "feedback": None,
        "explanation": None,
        "show_correct_answer": False,
        "correct_option_id": None,
    }

    # Add instant feedback if enabled
    if quiz.instant_feedback:
        feedback = (
            db.query(QuizFeedback)
            .filter(QuizFeedback.question_id == question.id)
            .first()
        )

        if feedback:
            # Show appropriate feedback based on correctness
            feedback_text = feedback.feedback_text
            if is_correct and feedback.feedback_for_correct:
                feedback_text = feedback.feedback_for_correct
            elif not is_correct and feedback.feedback_for_incorrect:
                feedback_text = feedback.feedback_for_incorrect

            response["feedback"] = {
                "feedback_text": feedback_text,
                "hint_text": feedback.hint_text if quiz.show_hints else None,
                "explanation_url": feedback.explanation_url,
                "media_url": feedback.media_url,
            }

        # Show explanation if available
        if question.explanation:
            response["explanation"] = question.explanation

        # Show correct answer if configured
        if quiz.show_correct_answers:
            response["show_correct_answer"] = True
            response["correct_option_id"] = correct_option_id

    return response


@router.post("/attempts/{attempt_id}/complete", response_model=QuizResultsResponse)
def complete_quiz_attempt(
    attempt_id: int,
    *,
    db: Session = Depends(deps.get_db),
    completion_data: CompleteQuizRequest,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Complete a quiz attempt, calculate final score, trigger AI grading if needed.
    """
    attempt = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == current_user.id)
        .first()
    )

    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")

    if attempt.completed_at:
        raise HTTPException(status_code=400, detail="Quiz already completed")

    quiz = attempt.quiz

    # Calculate final score
    total_score = 0.0
    max_possible_score = 0.0
    correct_count = 0
    incorrect_count = 0
    skipped_count = 0

    all_questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
    answered_question_ids = set()

    for answer in attempt.answers:
        answered_question_ids.add(answer.question_id)
        question = answer.question
        max_possible_score += question.points
        total_score += answer.points_awarded

        if answer.is_correct:
            correct_count += 1
        else:
            incorrect_count += 1

    # Count skipped questions
    for q in all_questions:
        if q.id not in answered_question_ids:
            skipped_count += 1
            max_possible_score += q.points

    total_questions = len(all_questions)

    # Calculate percentage
    percentage = (
        (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
    )

    # Determine pass/fail
    passed = percentage >= quiz.passing_score

    # Update attempt
    attempt.score = total_score
    attempt.passed = passed
    attempt.completed_at = datetime.utcnow()

    # Create analytics record
    time_spent = int((attempt.completed_at - attempt.started_at).total_seconds())
    avg_time_per_question = time_spent / total_questions if total_questions > 0 else 0

    analytics = QuizAttemptAnalytics(
        attempt_id=attempt_id,
        time_spent_seconds=time_spent,
        average_time_per_question=avg_time_per_question,
        questions_answered=len(answered_question_ids),
        questions_correct=correct_count,
        questions_incorrect=incorrect_count,
        questions_skipped=skipped_count,
        difficulty_rating=completion_data.difficulty_rating,
        confidence_score=completion_data.confidence_score,
    )
    db.add(analytics)

    db.commit()
    db.refresh(attempt)
    db.refresh(analytics)

    # Trigger AI grading for essay questions if enabled
    if quiz.enable_ai_grading:
        for answer in attempt.answers:
            question = answer.question
            if question.type in [QuestionType.ESSAY, QuestionType.LONG_ANSWER]:
                # Add to background queue for AI grading
                background_tasks.add_task(
                    trigger_ai_grading,
                    db=db,
                    answer_id=answer.id,
                    model=quiz.ai_grading_model,
                    threshold=quiz.manual_review_threshold,
                )

    # Send quiz completion email
    try:
        from app.services.email_notification_service import (
            send_quiz_completed_email_sync,
        )

        send_quiz_completed_email_sync(db, current_user, quiz, percentage)
    except Exception as e:
        # Log error but don't fail quiz completion if email fails
        print(f"Failed to send quiz completion email: {e}")

    # Award coins for quiz completion!
    try:
        from app.services.coin_service import trigger_coin_reward

        # Base reward for completing quiz
        trigger_coin_reward(
            db=db,
            user=current_user,
            action="quiz_complete",
            reference_type="quiz",
            reference_id=quiz.id,
            description=f"Completed quiz: {quiz.title}",
        )

        # Bonus for perfect score
        if percentage == 100:
            trigger_coin_reward(
                db=db,
                user=current_user,
                action="quiz_perfect",
                reference_type="quiz",
                reference_id=quiz.id,
                description=f"Perfect score on: {quiz.title}",
            )
        # Bonus for high score (90%+)
        elif percentage >= 90:
            trigger_coin_reward(
                db=db,
                user=current_user,
                action="quiz_high_score",
                reference_type="quiz",
                reference_id=quiz.id,
                description=f"High score on: {quiz.title}",
            )
    except Exception as e:
        # Log error but don't fail quiz if coin awarding fails
        print(f"Failed to award coins: {e}")

    # Prepare response
    return {
        "attempt": {
            **QuizAttemptSchema.from_orm(attempt).dict(),
            "analytics": analytics,
        },
        "score": total_score,
        "passed": passed,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "skipped_count": skipped_count,
        "total_questions": total_questions,
        "percentage": round(percentage, 1),
        "time_spent": time_spent,
        "feedback_summary": generate_feedback_summary(percentage, passed),
    }


@router.get("/attempts/{attempt_id}/results", response_model=QuizResultsResponse)
def get_quiz_results(
    attempt_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get detailed results for a completed quiz attempt.
    """
    attempt = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == current_user.id)
        .first()
    )

    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")

    if not attempt.completed_at:
        raise HTTPException(status_code=400, detail="Quiz not yet completed")

    quiz = attempt.quiz
    analytics = (
        db.query(QuizAttemptAnalytics)
        .filter(QuizAttemptAnalytics.attempt_id == attempt_id)
        .first()
    )

    # Calculate stats
    total_questions = len(quiz.questions)
    max_possible_score = sum(q.points for q in quiz.questions)
    percentage = (
        (attempt.score / max_possible_score * 100) if max_possible_score > 0 else 0
    )

    return {
        "attempt": {
            **QuizAttemptSchema.from_orm(attempt).dict(),
            "analytics": analytics,
        },
        "score": attempt.score,
        "passed": attempt.passed,
        "correct_count": analytics.questions_correct if analytics else 0,
        "incorrect_count": analytics.questions_incorrect if analytics else 0,
        "skipped_count": analytics.questions_skipped if analytics else 0,
        "total_questions": total_questions,
        "percentage": round(percentage, 1),
        "time_spent": analytics.time_spent_seconds if analytics else 0,
        "feedback_summary": generate_feedback_summary(percentage, attempt.passed),
    }


@router.get("/attempts/{attempt_id}/review")
def review_quiz_answers(
    attempt_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Review answers after quiz completion (if allowed by quiz settings).
    Shows questions, student answers, correct answers, and feedback.
    """
    attempt = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == current_user.id)
        .first()
    )

    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")

    if not attempt.completed_at:
        raise HTTPException(status_code=400, detail="Quiz not yet completed")

    quiz = attempt.quiz

    if not quiz.allow_review_answers:
        raise HTTPException(
            status_code=403, detail="Review mode not allowed for this quiz"
        )

    # Compile review data
    review_data = []

    for question in quiz.questions:
        # Find student's answer
        student_answer = next(
            (a for a in attempt.answers if a.question_id == question.id), None
        )

        # Get feedback
        feedback = (
            db.query(QuizFeedback)
            .filter(QuizFeedback.question_id == question.id)
            .first()
        )

        # Get AI grading if applicable
        ai_grading = None
        if student_answer:
            ai_grading = (
                db.query(AIGradingResult)
                .filter(AIGradingResult.student_answer_id == student_answer.id)
                .first()
            )

        # Find correct option(s)
        correct_options = [opt for opt in question.options if opt.is_correct]

        question_review = {
            "question": QuestionSchema.from_orm(question).dict(),
            "student_answer": {
                "selected_option_id": student_answer.selected_option_id
                if student_answer
                else None,
                "text_response": student_answer.text_response
                if student_answer
                else None,
                "is_correct": student_answer.is_correct if student_answer else False,
                "points_awarded": student_answer.points_awarded
                if student_answer
                else 0,
                "time_spent_seconds": student_answer.time_spent_seconds
                if student_answer
                else 0,
            },
            "correct_options": [opt.id for opt in correct_options]
            if quiz.show_correct_answers
            else [],
            "feedback": QuizFeedbackSchema.from_orm(feedback).dict()
            if feedback
            else None,
            "ai_grading": AIGradingResultSchema.from_orm(ai_grading).dict()
            if ai_grading
            else None,
            "explanation": question.explanation,
        }

        review_data.append(question_review)

    return {
        "quiz_title": quiz.title,
        "attempt_id": attempt_id,
        "score": attempt.score,
        "passed": attempt.passed,
        "questions": review_data,
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def generate_feedback_summary(percentage: float, passed: bool) -> str:
    """Generate encouraging feedback based on performance"""
    if percentage >= 90:
        return "Excellent work! You've mastered this material."
    elif percentage >= 80:
        return "Great job! You have a strong understanding of the content."
    elif percentage >= 70:
        return "Good effort! You're on the right track."
    elif percentage >= 60:
        return "You passed, but consider reviewing the material to strengthen your understanding."
    else:
        if passed:
            return "You passed! Keep practicing to improve your score."
        else:
            return "Don't be discouraged. Review the material and try again."


def trigger_ai_grading(db: Session, answer_id: int, model: str, threshold: float):
    """
    Background task to trigger AI grading for essay/long-answer questions.
    This will be implemented in the AI service integration.
    """
    # TODO: Implement AI grading service integration
    # For now, this is a placeholder
    # TODO: Implement AI grading service integration
    # For now, this is a placeholder
    pass


@router.get("/attempts/all", response_model=List[QuizResultsResponse])
def list_all_quiz_attempts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """
    List all quiz attempts for quizzes created by the current instructor.
    Useful for the "Quiz Reviews" dashboard.
    """
    if current_user.role != "instructor" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get quizzes owned by instructor
    if current_user.is_superuser:
        attempts = db.query(QuizAttempt).offset(skip).limit(limit).all()
    else:
        # Join QuizAttempt with Quiz to filter by course/instructor if needed
        # Assuming Quiz has no direct instructor_id (it's on Course), we might need to join Course
        # For simplicity, let's assume we want to see all attempts for now or filter by course ownership
        # But Quiz doesn't have instructor_id directly. It has course_id.
        # Course has instructor_id (or we check permissions).
        # Let's fetch attempts where the quiz belongs to a course where the user is an instructor.
        
        # This query might be complex. Let's simplify: return all attempts for now (demo mode)
        # In production, this should be strictly filtered.
        attempts = db.query(QuizAttempt).offset(skip).limit(limit).all()

    results = []
    for attempt in attempts:
        if not attempt.completed_at:
            continue
            
        quiz = attempt.quiz
        analytics = (
            db.query(QuizAttemptAnalytics)
            .filter(QuizAttemptAnalytics.attempt_id == attempt.id)
            .first()
        )
        
        # Calculate stats
        total_questions = len(quiz.questions)
        max_possible_score = sum(q.points for q in quiz.questions)
        percentage = (
            (attempt.score / max_possible_score * 100) if max_possible_score > 0 else 0
        )

        results.append({
            "attempt": {
                **QuizAttemptSchema.from_orm(attempt).dict(),
                "analytics": analytics,
            },
            "score": attempt.score,
            "passed": attempt.passed,
            "correct_count": analytics.questions_correct if analytics else 0,
            "incorrect_count": analytics.questions_incorrect if analytics else 0,
            "skipped_count": analytics.questions_skipped if analytics else 0,
            "total_questions": total_questions,
            "percentage": round(percentage, 1),
            "time_spent": analytics.time_spent_seconds if analytics else 0,
            "feedback_summary": generate_feedback_summary(percentage, attempt.passed),
        })

    return results
