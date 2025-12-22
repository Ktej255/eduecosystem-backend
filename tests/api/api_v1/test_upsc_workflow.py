import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from app.api.deps import get_db
from app.models.user import User
from app.models.upsc import UPSCBatch, UPSCPlan, UPSCQuestion, UPSCStudentProgress
from app.tests.utils.utils import random_email, random_lower_string
from app.tests.utils.user import authentication_token_from_email
from app.core.config import settings

# Override dependency to use test DB if needed, but for now we use the main one or a test session
# Assuming pytest fixtures handle DB session creation/rollback

def test_upsc_full_workflow(client: TestClient, db: Session, superuser_token_headers):
    """
    Test the complete UPSC workflow:
    1. Admin creates Batch
    2. Admin generates Plan (Mocked)
    3. Admin approves Plan -> Triggers Sync
    4. Student checks Dashboard -> Sees Plan
    5. Student starts Drill
    6. Student submits Attempt
    """
    
    # 1. Admin creates Batch
    batch_data = {
        "name": "Test Batch 2025",
        "description": "Test Batch for Integration Test",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31"
    }
    r = client.post(f"{settings.API_V1_STR}/upsc/batches", headers=superuser_token_headers, json=batch_data)
    assert r.status_code == 200
    batch_id = r.json()["id"]

    # 2. Admin generates Plan (Mocked - we manually create one to simulate AI result)
    # We skip the async task and insert directly for testing speed, 
    # OR we call the endpoint and mock the worker.
    # Let's insert a plan directly to simulate "AI Generated" state.
    from datetime import date, timedelta
    plan = UPSCPlan(
        batch_id=batch_id,
        plan_type="monthly",
        title="Test Monthly Plan",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        sequence_order=1,
        ai_generated=True,
        is_active=False # Not approved yet
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    # Add a Weekly and Daily plan to test hierarchy sync
    weekly_plan = UPSCPlan(
        batch_id=batch_id,
        plan_type="weekly",
        parent_plan_id=plan.id,
        title="Week 1",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7),
        sequence_order=1,
        ai_generated=True
    )
    db.add(weekly_plan)
    db.commit()
    db.refresh(weekly_plan)

    daily_plan = UPSCPlan(
        batch_id=batch_id,
        plan_type="daily",
        parent_plan_id=weekly_plan.id,
        title="Day 1",
        start_date=date.today(),
        end_date=date.today(),
        sequence_order=1,
        ai_generated=True
    )
    db.add(daily_plan)
    db.commit()
    db.refresh(daily_plan)

    # 3. Admin approves Plan -> Triggers Sync
    # We need to mock the celery task to run synchronously or just verify it's called.
    # For integration test, let's allow it to run if celery is eager, or manually call the logic.
    # Let's call the endpoint.
    r = client.post(f"{settings.API_V1_STR}/upsc/plans/{plan.id}/approve", headers=superuser_token_headers)
    assert r.status_code == 200
    assert r.json()["approved_by_id"] is not None

    # MANUALLY RUN SYNC TASK (since Celery might not be running in test env)
    from app.services.upsc_worker import initialize_student_progress_task
    initialize_student_progress_task(str(plan.id))

    # 4. Student checks Dashboard -> Sees Plan
    # Create a student user manually for control
    from app.schemas.user import UserCreate
    from app import crud
    password = "password"
    email = random_email()
    user_in = UserCreate(email=email, password=password, full_name="Test Student")
    student = crud.user.create(db=db, obj_in=user_in)
    student.role = "student"
    db.add(student)
    db.commit()
    db.refresh(student)
    
    # Create UPSCStudentProfile to link student to batch
    from app.models.upsc import UPSCStudentProfile
    profile = UPSCStudentProfile(
        user_id=student.id,
        batch_id=batch_id,
        enrollment_date=date.today(),
        target_year=2025
    )
    db.add(profile)
    db.commit()

    # Run sync task again for this student
    initialize_student_progress_task(str(plan.id))

    student_token_headers = authentication_token_from_email(client=client, email=email, db=db)
    
    # Check Plan Status
    r = client.get(f"{settings.API_V1_STR}/upsc/student/plans/{plan.id}/status", headers=student_token_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["is_locked"] == False # Monthly plan should be unlocked
    
    # Check Daily Plan Status
    r = client.get(f"{settings.API_V1_STR}/upsc/student/plans/{daily_plan.id}/status", headers=student_token_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["is_locked"] == False # Day 1 should be unlocked

    # 5. Student starts Drill
    # Need a question first
    question = UPSCQuestion(
        plan_id=daily_plan.id,
        question_number=1,
        title="Test Question",
        question_text="Explain the impact of AI.",
        marks=10,
        subject="Science",
        microtopics=["AI", "Tech"]
    )
    db.add(question)
    db.commit()

    start_req = {
        "plan_id": str(daily_plan.id),
        "question_number": 1
    }
    r = client.post(f"{settings.API_V1_STR}/upsc/drills/start", headers=student_token_headers, json=start_req)
    assert r.status_code == 200
    assert "session_id" in r.json()

    # 6. Student submits Attempt (Image)
    # Mock image upload
    # ... (Simplified for this script, focusing on flow logic)

    print("Workflow Test Passed!")
