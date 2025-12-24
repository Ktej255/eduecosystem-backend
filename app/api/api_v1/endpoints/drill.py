"""
API endpoints for Daily Drill System
Handles drill sessions, answer uploads, and report generation
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.services.drill_report_service import drill_report_service
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.drill import DrillQuestion, DrillContent, DrillModelAnswer, DrillSession, DrillDailySummary

router = APIRouter()


# Request/Response Models
class DrillSessionStart(BaseModel):
    date: str
    question_number: int  # 1, 2, or 3


class AnswerUpload(BaseModel):
    date: str
    question_number: int
    answer_type: str  # "before" or "after"
    answer_text: str  # OCR extracted text or manual input
    image_base64: Optional[str] = None


class ReportRequest(BaseModel):
    date: str
    question_number: int
    question_text: str
    model_answer: str
    before_answer_text: str
    after_answer_text: str
    content_summary: str


class DailySummaryRequest(BaseModel):
    date: str
    question_reports: List[dict]
    yesterday_date: Optional[str] = None


@router.post("/start-session")
async def start_drill_session(
    request: DrillSessionStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a new drill session for a specific date and question
    Returns question data, content, and model answer
    """
    # Fetch the 3 most recent questions
    # In a real scenario, we might want a more sophisticated scheduling system
    questions = db.query(DrillQuestion).order_by(desc(DrillQuestion.created_at)).limit(3).all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions available. Please ask admin to create questions.")
    
    # Map 1, 2, 3 to index 0, 1, 2
    idx = request.question_number - 1
    if idx < 0 or idx >= len(questions):
        raise HTTPException(status_code=404, detail="Question not found")
        
    question = questions[idx]
    
    # Format response to match frontend expectations
    return {
        "success": True,
        "data": {
            "id": str(question.id),
            "title": f"{question.gs_paper} - {question.topic}",
            "text": question.question_text,
            "points": question.key_points or [],
            "content": {
                "title": question.content.title if question.content else "Content not available",
                "sections": question.content.sections if question.content else []
            } if question.content else None,
            "model_answer": {
                "title": question.model_answer.title if question.model_answer else "Model Answer",
                "text": question.model_answer.answer_text if question.model_answer else "Not available",
                "keyPoints": question.model_answer.key_points if question.model_answer else []
            } if question.model_answer else None
        }
    }


@router.post("/upload-answer")
async def upload_answer(
    request: AnswerUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload student answer (before or after reading content)
    Stores image and extracted text
    """
    # 1. Find the question
    questions = db.query(DrillQuestion).order_by(desc(DrillQuestion.created_at)).limit(3).all()
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found")
        
    idx = request.question_number - 1
    if idx < 0 or idx >= len(questions):
        raise HTTPException(status_code=404, detail="Question not found")
        
    question = questions[idx]
    
    # 2. Find or create session
    # Convert date string to date object
    try:
        session_date = datetime.strptime(request.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    session = db.query(DrillSession).filter(
        DrillSession.student_id == current_user.id,
        DrillSession.date == session_date,
        DrillSession.question_id == str(question.id)
    ).first()
    
    if not session:
        session = DrillSession(
            student_id=current_user.id,
            date=session_date,
            question_id=str(question.id),
            question_number=request.question_number
        )
        db.add(session)
        # Flush to get ID if needed, though we commit later
    
    # 3. Update answer
    if request.answer_type == "before":
        session.before_answer_text = request.answer_text
        # session.before_answer_image_url = ... (handle image upload if needed)
    elif request.answer_type == "after":
        session.after_answer_text = request.answer_text
        # session.after_answer_image_url = ...
        
    db.commit()
    
    return {
        "success": True,
        "message": f"{request.answer_type.capitalize()} answer uploaded successfully",
        "answer_id": str(session.id)
    }


@router.post("/generate-report")
async def generate_question_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI-powered performance report for a single question using Grok 4.1
    """
    try:
        report = await drill_report_service.generate_question_report(
            question_text=request.question_text,
            model_answer=request.model_answer,
            before_answer_text=request.before_answer_text,
            after_answer_text=request.after_answer_text,
            content_summary=request.content_summary,
            user=current_user
        )
        
        # Find or create session
        # Similar logic to upload_answer to ensure we have the session
        questions = db.query(DrillQuestion).order_by(desc(DrillQuestion.created_at)).limit(3).all()
        if questions:
            idx = request.question_number - 1
            if 0 <= idx < len(questions):
                question = questions[idx]
                
                session = db.query(DrillSession).filter(
                    DrillSession.student_id == current_user.id,
                    DrillSession.date == request.date,
                    DrillSession.question_id == str(question.id)
                ).first()
                
                if not session:
                    session = DrillSession(
                        student_id=current_user.id,
                        date=request.date,
                        question_id=str(question.id),
                        question_number=request.question_number
                    )
                    db.add(session)
                
                # Update session with report data
                session.report_data = report
                session.before_score = report.get("before_score")
                session.after_score = report.get("after_score")
                session.improvement = report.get("improvement")
                session.overall_score = report.get("overall_score")
                session.completed_at = datetime.utcnow()
                
                db.commit()
        
        return {
            "success": True,
            "report": report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.post("/daily-summary")
async def generate_daily_summary(
    request: DailySummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate daily summary report for all 3 questions using Grok 4.1
    Includes comparison with yesterday's performance
    """
    try:
        # Fetch yesterday's summary from database
        yesterday_summary_data = None
        if request.yesterday_date:
            yesterday_summary = db.query(DrillDailySummary).filter(
                DrillDailySummary.student_id == current_user.id,
                DrillDailySummary.date == request.yesterday_date
            ).first()
            
            if yesterday_summary:
                yesterday_summary_data = {
                    "overall_score": yesterday_summary.overall_score,
                    "average_improvement": yesterday_summary.average_improvement
                }
        
        summary = await drill_report_service.generate_daily_summary(
            question_reports=request.question_reports,
            date=request.date,
            yesterday_summary=yesterday_summary_data,
            user=current_user
        )
        
        # Store summary in database
        try:
            # Check if summary already exists for today
            existing_summary = db.query(DrillDailySummary).filter(
                DrillDailySummary.student_id == current_user.id,
                DrillDailySummary.date == request.date
            ).first()
            
            if existing_summary:
                # Update existing
                existing_summary.overall_score = summary.get("overall_score")
                existing_summary.average_improvement = summary.get("average_improvement")
                existing_summary.total_time_spent = summary.get("total_time_spent")
                existing_summary.question_scores = summary.get("question_scores")
                existing_summary.comparison_data = summary.get("comparison")
                existing_summary.strengths = summary.get("strengths")
                existing_summary.challenges = summary.get("challenges")
                existing_summary.recommendations = summary.get("recommendations")
                existing_summary.insights = summary.get("insights")
            else:
                # Create new
                new_summary = DrillDailySummary(
                    student_id=current_user.id,
                    date=request.date,
                    overall_score=summary.get("overall_score"),
                    average_improvement=summary.get("average_improvement"),
                    total_time_spent=summary.get("total_time_spent"),
                    question_scores=summary.get("question_scores"),
                    comparison_data=summary.get("comparison"),
                    strengths=summary.get("strengths"),
                    challenges=summary.get("challenges"),
                    recommendations=summary.get("recommendations"),
                    insights=summary.get("insights")
                )
                db.add(new_summary)
            
            db.commit()
        except Exception as db_e:
            print(f"Failed to save summary to DB: {db_e}")
            # Don't fail the request if DB save fails, just return the summary
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@router.get("/session-status/{date}")
async def get_session_status(
    date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current status of drill session for a date
    Returns progress, completed questions, etc.
    """
    # Fetch sessions for this date
    sessions = db.query(DrillSession).filter(
        DrillSession.student_id == current_user.id,
        DrillSession.date == date
    ).all()
    
    completed_questions = [s.question_number for s in sessions if s.report_data]
    
    # Determine current question (next available)
    current_question = 1
    if completed_questions:
        current_question = max(completed_questions) + 1
        if current_question > 3:
            current_question = 3  # Stay on 3 if all done
            
    # Check if we have an ongoing session (started but not completed)
    # This logic might need refinement based on how "ongoing" is defined
    # For now, we assume if it's not in completed_questions, it's new
    
    return {
        "success": True,
        "status": {
            "date": date,
            "current_question": current_question,
            "current_step": 1, # Default to step 1
            "completed_questions": completed_questions,
            "has_ongoing_session": False # Simplified for now
        }
    }


@router.get("/dashboard-analytics")
async def get_dashboard_analytics(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get drill analytics for dashboard
    Returns last N days of performance data
    """
    # Fetch daily summaries
    summaries = db.query(DrillDailySummary).filter(
        DrillDailySummary.student_id == current_user.id
    ).order_by(desc(DrillDailySummary.date)).limit(days).all()
    
    # Calculate stats
    total_questions = 0
    total_score = 0
    total_improvement = 0
    
    daily_scores = []
    
    for s in summaries:
        daily_scores.append({
            "date": s.date.isoformat(),
            "score": s.overall_score,
            "improvement": s.average_improvement
        })
        total_score += s.overall_score or 0
        total_improvement += s.average_improvement or 0
        # Assuming 3 questions per summary for simplicity, or check question_scores
        total_questions += 3 
        
    count = len(summaries)
    avg_score = total_score / count if count > 0 else 0
    avg_improvement = total_improvement / count if count > 0 else 0
    
    return {
        "success": True,
        "analytics": {
            "last_7_days": {
                "average_score": round(avg_score, 1),
                "average_improvement": round(avg_improvement, 1),
                "total_questions": total_questions,
                "completion_rate": 100 if count > 0 else 0 # Placeholder
            },
            "daily_scores": daily_scores,
            "strengths": summaries[0].strengths if summaries else [],
            "challenges": summaries[0].challenges if summaries else []
        }
    }
