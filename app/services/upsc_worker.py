import json
import logging
from datetime import datetime, timedelta
from uuid import UUID
from typing import List, Dict, Any

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.email import send_email
from app.db.session import SessionLocal
from app.models.upsc import UPSCPlan, UPSCQuestion, UPSCBatch, UPSCAttempt, UPSCReport, UPSCContent, UPSCStudentProgress, UPSCStudentProfile
from app.models.notification import NotificationType, NotificationPriority
from app.services.notification_helpers import create_and_emit_notification
from app.services.ocr import get_reader # Reuse EasyOCR for now as fallback
from app.models.user import User

from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize Grok client (using OpenAI SDK)
client = OpenAI(
    api_key=settings.GROK_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL if "openrouter" in settings.OPENROUTER_BASE_URL else "https://api.x.ai/v1"
)

@celery_app.task(name="generate_ai_plan")
def generate_ai_plan_task(request_data: Dict[str, Any]):
    """
    Generate a monthly/weekly/daily plan structure using Grok AI.
    """
    db = SessionLocal()
    try:
        batch_id = request_data.get("batch_id")
        subject = request_data.get("subject")
        start_date = datetime.strptime(request_data.get("start_date"), "%Y-%m-%d").date()
        total_days = request_data.get("total_days", 21)
        topics = request_data.get("topics", [])

        logger.info(f"Generating plan for batch {batch_id}, subject {subject}")

        # 1. Construct Prompt
        prompt = f"""
        Create a detailed {total_days}-day study plan for UPSC Mains Subject: {subject}.
        Focus Topics: {', '.join(topics)}.
        
        Structure:
        - Divide into Weekly Plans (e.g., Week 1, Week 2, Week 3).
        - Each Week has Daily Plans (Day 1 to Day 7).
        - Each Day must have exactly 3 Questions.
        
        Output JSON format ONLY:
        {{
            "weeks": [
                {{
                    "week_number": 1,
                    "title": "Week 1 Theme",
                    "days": [
                        {{
                            "day_number": 1,
                            "title": "Day 1 Topic",
                            "questions": [
                                {{
                                    "question_number": 1,
                                    "title": "Question Title",
                                    "text": "Full Question Text",
                                    "marks": 10,
                                    "microtopics": ["topic1", "topic2"]
                                }},
                                ... (3 questions total)
                            ]
                        }},
                        ... (7 days total)
                    ]
                }},
                ...
            ]
        }}
        """

        # 2. Call Grok API
        response = client.chat.completions.create(
            model="google/gemma-3-27b-it",  # Google Gemma 3 27B
            messages=[
                {"role": "system", "content": "You are an expert UPSC curriculum planner."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        plan_json = json.loads(response.choices[0].message.content)

        # 3. Save to Database
        # Create Monthly Plan (Root)
        monthly_plan = UPSCPlan(
            batch_id=batch_id,
            plan_type="monthly",
            title=f"{subject} - Monthly Plan",
            start_date=start_date,
            end_date=start_date + timedelta(days=total_days),
            sequence_order=1,
            ai_generated=True,
            plan_data=plan_json
        )
        db.add(monthly_plan)
        db.commit()
        db.refresh(monthly_plan)

        current_date = start_date
        
        # Create Weekly & Daily Plans
        for week in plan_json.get("weeks", []):
            weekly_plan = UPSCPlan(
                batch_id=batch_id,
                plan_type="weekly",
                parent_plan_id=monthly_plan.id,
                title=week.get("title", f"Week {week['week_number']}"),
                start_date=current_date,
                end_date=current_date + timedelta(days=6),
                sequence_order=week['week_number'],
                ai_generated=True
            )
            db.add(weekly_plan)
            db.commit()
            db.refresh(weekly_plan)

            for day in week.get("days", []):
                daily_plan = UPSCPlan(
                    batch_id=batch_id,
                    plan_type="daily",
                    parent_plan_id=weekly_plan.id,
                    title=day.get("title", f"Day {day['day_number']}"),
                    start_date=current_date,
                    end_date=current_date,
                    sequence_order=day['day_number'],
                    ai_generated=True
                )
                db.add(daily_plan)
                db.commit()
                db.refresh(daily_plan)

                # Add Questions
                for q in day.get("questions", []):
                    question = UPSCQuestion(
                        plan_id=daily_plan.id,
                        question_number=q['question_number'],
                        title=q['title'],
                        question_text=q['text'],
                        marks=q['marks'],
                        subject=subject,
                        microtopics=q['microtopics']
                    )
                    db.add(question)
                
                current_date += timedelta(days=1)
        
        db.commit()
        logger.info("Plan generation completed successfully.")

        # Send Notification & Email
        # Assuming we know who requested it or notify all admins/students in batch
        # For now, let's notify the batch creator (if available) or just log
        # In a real scenario, we'd notify the user who triggered it.
        # Let's assume request_data has 'user_id'
        user_id = request_data.get("user_id")
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # Email
                send_email(
                    email_to=user.email,
                    subject="Your UPSC Plan is Ready",
                    template_name="upsc_plan_ready.html",
                    template_body={
                        "name": user.full_name,
                        "subject": subject,
                        "link": f"{settings.SERVER_HOST}/student/plans" 
                    }
                )
                
                # In-App Notification
                create_and_emit_notification(
                    db=db,
                    user_id=user.id,
                    type=NotificationType.UPSC_PLAN_GENERATED,
                    title="Plan Generated",
                    message=f"Your study plan for {subject} is ready.",
                    priority=NotificationPriority.NORMAL,
                    action_url="/student/plans"
                )

        return {"status": "success", "plan_id": str(monthly_plan.id)}

    except Exception as e:
        logger.error(f"Error generating plan: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(name="analyze_answer")
def analyze_answer_task(attempt_id: str):
    """
    Perform OCR and AI analysis on a student's answer attempt.
    """
    db = SessionLocal()
    try:
        attempt = db.query(UPSCAttempt).filter(UPSCAttempt.id == attempt_id).first()
        if not attempt:
            return {"status": "error", "message": "Attempt not found"}

        # 1. Perform OCR (Placeholder for S3 download + OCR)
        # In production: download image from attempt.image_url
        # For now, we assume local path or mock
        ocr_text = ""
        try:
            # Mocking OCR for now or using EasyOCR if local file
            # reader = get_reader()
            # result = reader.readtext(attempt.image_url, detail=0)
            # ocr_text = " ".join(result)
            ocr_text = "Student answer text extracted via OCR..." # Placeholder
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            ocr_text = "[OCR Failed]"

        attempt.answer_text = ocr_text
        db.commit()

        # If this is the 'after' attempt, trigger full comparison report
        if attempt.attempt_type == 'after':
            # Find the 'before' attempt
            before_attempt = db.query(UPSCAttempt).filter(
                UPSCAttempt.student_id == attempt.student_id,
                UPSCAttempt.question_id == attempt.question_id,
                UPSCAttempt.attempt_type == 'before'
            ).first()

            if before_attempt:
                generate_comparison_report(db, before_attempt, attempt)

        return {"status": "success", "ocr_text": ocr_text}

    except Exception as e:
        logger.error(f"Error analyzing answer: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

def generate_comparison_report(db, before: UPSCAttempt, after: UPSCAttempt):
    """
    Helper to generate comparison report using Grok.
    """
    question = db.query(UPSCQuestion).filter(UPSCQuestion.id == before.question_id).first()
    model_answer = db.query(UPSCContent).filter(
        UPSCContent.question_id == question.id, 
        UPSCContent.content_type == 'model_answer'
    ).first()
    
    model_text = model_answer.content_text if model_answer else "No model answer provided."

    prompt = f"""
    Compare these two student answers for UPSC Mains.
    
    Question: {question.question_text}
    Marks: {question.marks}
    Microtopics: {question.microtopics}
    
    Model Answer: {model_text}
    
    Attempt 1 (Before Study): {before.answer_text}
    Attempt 2 (After Study): {after.answer_text}
    
    Provide a JSON report:
    {{
        "before": {{ "coverage": 0-100, "similarity": 0-100, "marks": 0-{question.marks} }},
        "after": {{ "coverage": 0-100, "similarity": 0-100, "marks": 0-{question.marks} }},
        "missed_points": ["point1", "point2"],
        "suggestions": ["tip1", "tip2"],
        "tone_feedback": "text"
    }}
    """
    
    response = client.chat.completions.create(
        model="google/gemma-3-27b-it",  # Google Gemma 3 27B
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    
    report = UPSCReport(
        student_id=before.student_id,
        question_id=question.id,
        attempt_before_id=before.id,
        attempt_after_id=after.id,
        coverage_before=result['before']['coverage'],
        similarity_before=result['before']['similarity'],
        estimated_marks_before=result['before']['marks'],
        coverage_after=result['after']['coverage'],
        similarity_after=result['after']['similarity'],
        estimated_marks_after=result['after']['marks'],
        missed_points=result.get('missed_points'),
        suggestions=result.get('suggestions'),
        tone_feedback=result.get('tone_feedback'),
        raw_ai_output=result
    )
    db.add(report)
    db.commit()

    # Notify Student
    student = db.query(User).filter(User.id == before.student_id).first()
    if student:
        # Email
        send_email(
            email_to=student.email,
            subject="Your UPSC Drill Report is Ready",
            template_name="upsc_report_ready.html",
            template_body={
                "name": student.full_name,
                "topic": question.title,
                "link": f"{settings.SERVER_HOST}/student/reports/{report.id}"
            }
        )
        
        # In-App Notification
        create_and_emit_notification(
            db=db,
            user_id=student.id,
            type=NotificationType.UPSC_REPORT_READY,
            title="Drill Report Ready",
            message=f"Analysis for '{question.title}' is available.",
            priority=NotificationPriority.HIGH,
            action_url=f"/student/reports/{report.id}"
        )

@celery_app.task(name="transcribe_audio")
def transcribe_audio_task(attempt_id: str, file_path: str):
    """
    Transcribe audio file using OpenAI Whisper.
    """
    db = SessionLocal()
    try:
        attempt = db.query(UPSCAttempt).filter(UPSCAttempt.id == attempt_id).first()
        if not attempt:
            return {"status": "error", "message": "Attempt not found"}

        # Use OpenAI client for transcription (Whisper)
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        
        attempt.transcription = transcription.text
        # Also set answer_text for consistency if it's empty
        if not attempt.answer_text:
            attempt.answer_text = transcription.text
            
        db.commit()
        
        # Cleanup file
        import os
        if os.path.exists(file_path):
            os.remove(file_path)

        return {"status": "success", "text": transcription.text}

    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(name="send_daily_reminders")
def send_daily_reminders_task():
    """
    Check for pending daily drills and send reminders.
    Run this periodically (e.g., every morning).
    """
    db = SessionLocal()
    try:
        # Find students with incomplete daily plans for today
        today = datetime.utcnow().date()
        
        # Get active daily plans for today
        active_plans = db.query(UPSCPlan).filter(
            UPSCPlan.plan_type == 'daily',
            UPSCPlan.start_date == today
        ).all()

        for plan in active_plans:
            # Get students in the batch
            # Assuming we can get students via batch -> student_profiles -> user
            # For simplicity, let's iterate through student_progress if initialized, 
            # or just find all students in batch.
            
            # Let's use UPSCStudentProgress to find who hasn't completed it
            pending_progress = db.query(UPSCStudentProgress).filter(
                UPSCStudentProgress.plan_id == plan.id,
                UPSCStudentProgress.completion_percentage < 100.0
            ).all()

            for progress in pending_progress:
                student = db.query(User).filter(User.id == progress.student_id).first()
                if student:
                    # Send Email
                    send_email(
                        email_to=student.email,
                        subject="UPSC Drill Reminder",
                        template_name="upsc_drill_reminder.html",
                        template_body={
                            "name": student.full_name,
                            "title": plan.title,
                            "link": f"{settings.SERVER_HOST}/student/dashboard"
                        }
                    )
                    
                    # In-App Notification
                    create_and_emit_notification(
                        db=db,
                        user_id=student.id,
                        type=NotificationType.UPSC_DRILL_REMINDER,
                        title="Daily Drill Reminder",
                        message=f"Don't forget to complete '{plan.title}' today!",
                        priority=NotificationPriority.NORMAL,
                        action_url="/student/dashboard"
                    )
                    
        return {"status": "success", "reminders_sent": len(active_plans)} # Simplified count

    except Exception as e:
        logger.error(f"Error sending reminders: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(name="initialize_student_progress")
def initialize_student_progress_task(plan_id: str):
    """
    Initialize progress records for all students in the batch when a plan is approved.
    """
    db = SessionLocal()
    try:
        # 1. Fetch the plan
        plan = db.query(UPSCPlan).filter(UPSCPlan.id == plan_id).first()
        if not plan:
            return {"status": "error", "message": "Plan not found"}

        # 2. Fetch all students in the batch
        # Use UPSCStudentProfile to find students enrolled in this batch
        students = db.query(User).join(UPSCStudentProfile).filter(UPSCStudentProfile.batch_id == plan.batch_id).all()
        
        if not students:
            logger.warning(f"No students found for batch {plan.batch_id}")
            return {"status": "warning", "message": "No students found in batch"}

        # 3. Get all sub-plans (weeks, days)
        # We need to initialize progress for the Monthly plan AND its children?
        # Or just the daily plans?
        # Usually, we track progress on the granular items (Daily).
        # But we might want to lock/unlock Weeks too.
        
        all_plans_in_hierarchy = db.query(UPSCPlan).filter(
            (UPSCPlan.id == plan.id) | (UPSCPlan.parent_plan_id == plan.id)
        ).all()
        
        # This only gets 1 level down. We need recursive or just fetch all for batch?
        # Let's fetch all plans for this batch that are part of this hierarchy.
        # Actually, simpler: Fetch all plans for the batch, or just use the known structure.
        # If plan is Monthly, we want its Weeks and Days.
        # Let's fetch all plans where root is this plan.
        # Since we don't have 'root_plan_id', we might need to traverse.
        # For MVP, let's assume 3 levels: Monthly -> Weekly -> Daily.
        
        # Fetch Weekly plans
        weekly_plans = db.query(UPSCPlan).filter(UPSCPlan.parent_plan_id == plan.id).all()
        weekly_ids = [p.id for p in weekly_plans]
        
        # Fetch Daily plans
        daily_plans = db.query(UPSCPlan).filter(UPSCPlan.parent_plan_id.in_(weekly_ids)).all()
        
        all_target_plans = [plan] + weekly_plans + daily_plans

        count = 0
        for student in students:
            for p in all_target_plans:
                # Check if progress already exists
                exists = db.query(UPSCStudentProgress).filter(
                    UPSCStudentProgress.student_id == student.id,
                    UPSCStudentProgress.plan_id == p.id
                ).first()
                
                if not exists:
                    # Determine Lock Status
                    is_locked = True
                    
                    # Unlock Rules:
                    # 1. Monthly Plan (Root) -> Unlocked
                    if p.id == plan.id:
                        is_locked = False
                    
                    # 2. First Week -> Unlocked
                    if p.plan_type == 'weekly' and p.sequence_order == 1:
                        is_locked = False
                        
                    # 3. First Day of First Week -> Unlocked
                    # We need to check if parent is Week 1
                    if p.plan_type == 'daily':
                        parent = next((w for w in weekly_plans if w.id == p.parent_plan_id), None)
                        if parent and parent.sequence_order == 1 and p.sequence_order == 1:
                            is_locked = False

                    progress = UPSCStudentProgress(
                        student_id=student.id,
                        plan_id=p.id,
                        is_locked=is_locked,
                        completion_percentage=0.0
                    )
                    db.add(progress)
                    count += 1
        
        db.commit()
        return {"status": "success", "records_created": count}

    except Exception as e:
        logger.error(f"Error initializing progress: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
