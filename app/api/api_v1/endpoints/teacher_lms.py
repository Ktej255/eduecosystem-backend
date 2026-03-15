from typing import Any, List, Optional
import csv
import json
import io
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID

from app.api import deps
from app.models.lms import Assignment, StudentSubmission, AIEvaluationLog
from app.models.question_bank import QuestionBank, BankQuestion
from app.models.user import User
from app.schemas.lms import (
    LMSAssignment,
    LMSAssignmentCreate,
    LMSAssignmentUpdate,
    StudentSubmission as StudentSubmissionSchema,
    StudentSubmissionDetailed,
    AIEvaluationLog as AIEvaluationLogSchema,
    AIEvaluationLogUpdate
)
from app.schemas.question_bank import BankQuestion as BankQuestionSchema
from app.services.gemini_service import gemini_service
from app.schemas.user import UserBasic

from app.schemas.lms_schemas import BulkQuestionUpload, QuestionResponse
from app.models.lms import Assignment, StudentSubmission, AIEvaluationLog, Question, Option

router = APIRouter()

@router.post("/questions/bulk", response_model=dict)
async def bulk_upload_questions_json(
    *,
    db: Session = Depends(deps.get_db),
    payload: BulkQuestionUpload,
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Bulk upload MCQs from JSON payload (sent from frontend staging area).
    Includes AI tagging for UPSC subjects.
    """
    questions_to_insert = payload.questions
    if not questions_to_insert:
        return {"status": "success", "inserted": 0}

    # Extract question texts for AI tagging
    question_texts = [q.text for q in questions_to_insert]
    
    # AI Tagging pass
    try:
        tags = gemini_service.auto_tag_upsc_topics(question_texts)
    except Exception as e:
        print(f"AI Tagging failed: {e}")
        tags = ["General"] * len(question_texts)

    inserted_count = 0
    
    try:
        for i, q_data in enumerate(questions_to_insert):
            # Create Question
            db_question = Question(
                teacher_id=current_user.id,
                text=q_data.text,
                explanation=q_data.explanation,
                subject_tag=tags[i] if i < len(tags) else "General",
                difficulty=q_data.difficulty or "medium"
            )
            db.add(db_question)
            db.flush() # Get ID for options

            # Create Options
            for opt_data in q_data.options:
                db_option = Option(
                    question_id=db_question.id,
                    text=opt_data.text,
                    is_correct=opt_data.is_correct
                )
                db.add(db_option)
            
            inserted_count += 1
        
        db.commit()
        return {
            "status": "success", 
            "inserted": inserted_count, 
            "tags_generated": len(tags)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")

@router.get("/my-students", response_model=List[UserBasic])
def get_my_students(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Get all students (migrated from admin/users for teacher context).
    """
    students = db.query(User).filter(User.role == "student").all()
    return students

@router.get("/assignments", response_model=List[LMSAssignment])
def get_teacher_assignments(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Get all assignments for the teacher's batches.
    """
    return db.query(Assignment).all()

@router.post("/assignments", response_model=LMSAssignment)
def create_teacher_assignment(
    *,
    db: Session = Depends(deps.get_db),
    assignment_in: LMSAssignmentCreate,
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Create a new assignment with a rubric.
    """
    db_obj = Assignment(**assignment_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/assignments/{assignment_id}/submissions", response_model=List[StudentSubmissionDetailed])
def get_assignment_submissions(
    assignment_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Get all student submissions for a specific assignment.
    """
    submissions = db.query(StudentSubmission).filter(
        StudentSubmission.assignment_id == assignment_id
    ).all()
    
    results = []
    for sub in submissions:
        student = db.query(User).filter(User.id == sub.student_id).first()
        sub_detailed = StudentSubmissionDetailed.model_validate(sub)
        sub_detailed.student_name = student.full_name if student else "Unknown Student"
        results.append(sub_detailed)
        
    return results

@router.get("/submissions/{submission_id}", response_model=StudentSubmissionDetailed)
def get_student_submission(
    submission_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Get details of a specific student submission.
    """
    submission = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    student = db.query(User).filter(User.id == submission.student_id).first()
    sub_detailed = StudentSubmissionDetailed.model_validate(submission)
    sub_detailed.student_name = student.full_name if student else "Unknown Student"
    return sub_detailed

@router.post("/submissions/{submission_id}/evaluate", response_model=AIEvaluationLogSchema)
async def trigger_ai_evaluation(
    submission_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Trigger AI evaluation for a single submission using Gemini.
    """
    submission = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    assignment = submission.assignment
    if not assignment or not assignment.rubric_json:
        raise HTTPException(status_code=400, detail="Assignment rubric missing")

    try:
        # Construct prompt for Gemini
        rubric_str = json.dumps(assignment.rubric_json)
        prompt = f"""You are an expert academic evaluator. Evaluate the following student essay based on the provided rubric.
        
RUBRIC:
{rubric_str}

STUDENT ESSAY:
{submission.content_text}

Provide a structured evaluation including a numerical score (0-100) and detailed feedback on strengths, weaknesses, and specific directives for improvement.
Return JSON ONLY in this format:
{{
    "score": 0-100,
    "feedback": {{
        "strengths": ["point 1", "point 2"],
        "weaknesses": ["point 1", "point 2"],
        "directive_feedback": "Specific advice for the student"
    }}
}}
"""
        
        # Call Gemini Service
        response_text = gemini_service.generate_text(prompt, user=current_user, temperature=0.3)
        
        # Parse JSON from response
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        ai_data = json.loads(clean_json)
        
        eval_log = AIEvaluationLog(
            submission_id=submission.id,
            ai_score=float(ai_data.get("score", 0)),
            ai_feedback_json=ai_data.get("feedback", {}),
            status="draft"
        )
        db.add(eval_log)
        
        submission.status = "evaluated"
        db.add(submission)
        
        db.commit()
        db.refresh(eval_log)
        return eval_log
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"AI Evaluation failed: {str(e)}")

@router.post("/assignments/{assignment_id}/bulk-evaluate", response_model=List[AIEvaluationLogSchema])
async def bulk_evaluate_submissions(
    assignment_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Trigger AI evaluation for all pending submissions of an assignment.
    """
    submissions = db.query(StudentSubmission).filter(
        StudentSubmission.assignment_id == assignment_id,
        StudentSubmission.status == "pending"
    ).all()
    
    results = []
    for submission in submissions:
        # Note: In production, this should be handled by a background task (e.g., Celery)
        try:
            # Reusing the evaluation logic (ideally refactored into a service)
            # For brevity in this snippet, we call the trigger_ai_evaluation logic or a mock
            # For now, let's assume we call a internal helper
            eval_log = await trigger_ai_evaluation(submission.id, db, current_user)
            results.append(eval_log)
        except:
            continue
            
    return results

@router.put("/evaluations/{evaluation_id}", response_model=AIEvaluationLogSchema)
def update_evaluation(
    evaluation_id: UUID,
    *,
    db: Session = Depends(deps.get_db),
    eval_in: AIEvaluationLogUpdate,
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Update an AI evaluation (e.g., teacher approves or edits score).
    """
    eval_log = db.query(AIEvaluationLog).filter(AIEvaluationLog.id == evaluation_id).first()
    if not eval_log:
        raise HTTPException(status_code=404, detail="Evaluation log not found")
    
    update_data = eval_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(eval_log, field, value)
    
    db.add(eval_log)
    db.commit()
    db.refresh(eval_log)
    return eval_log

@router.post("/question-banks/{bank_id}/bulk-upload", response_model=List[BankQuestionSchema])
async def bulk_upload_questions(
    bank_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_instructor),
) -> Any:
    """
    Bulk upload MCQs from a CSV file into a question bank.
    CSV format: text, type, points, difficulty, options(JSON), correct_answer, explanation, tags
    """
    bank = db.query(QuestionBank).filter(QuestionBank.id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Question bank not found")

    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    
    questions = []
    for row in reader:
        try:
            db_question = BankQuestion(
                instructor_id=current_user.id,
                text=row["text"],
                type=row.get("type", "multiple_choice"),
                points=int(row.get("points", 1)),
                difficulty=row.get("difficulty", "medium"),
                options=row.get("options"),
                correct_answer=row.get("correct_answer"),
                explanation=row.get("explanation"),
                tags=row.get("tags")
            )
            db.add(db_question)
            db.flush() # Get ID
            bank.questions.append(db_question)
            questions.append(db_question)
        except Exception as e:
            print(f"Error parsing CSV row: {e}")
            continue
            
    db.commit()
    for q in questions:
        db.refresh(q)
    return questions
