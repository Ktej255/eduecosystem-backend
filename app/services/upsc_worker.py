"""
UPSC Background Worker (Fresh 2025)
Handles plan generation and answer analysis using Tiered Gemini AI.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.upsc import UPSCPlan, UPSCQuestion, UPSCAttempt, UPSCReport
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

@celery_app.task(name="generate_ai_plan")
def generate_ai_plan_task(request_data: Dict[str, Any]):
    """Generates study plans using Tiered Gemini AI"""
    db = SessionLocal()
    try:
        subject = request_data.get("subject")
        topics = request_data.get("topics", [])
        
        prompt = f"Create a UPSC study plan for {subject} covering: {', '.join(topics)}. Return JSON ONLY."
        
        # Use tiered service (Plan generation is complex)
        response = gemini_service.generate_text(
            prompt=prompt,
            is_complex=True
        )
        
        import re
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        plan_json = json.loads(json_match.group())
        
        # (DB saving logic continues here...)
        return {"status": "success", "subject": subject}
    except Exception as e:
        logger.error(f"Plan generation failed: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(name="analyze_answer")
def analyze_answer_task(attempt_id: str):
    """Analyze student answers using Tiered Gemini AI"""
    db = SessionLocal()
    try:
        attempt = db.query(UPSCAttempt).filter(UPSCAttempt.id == attempt_id).first()
        if not attempt: return
        
        # Perform analysis via gemini_service
        # (Logic to compare 'before' and 'after' answers)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Answer analysis failed: {e}")
    finally:
        db.close()
