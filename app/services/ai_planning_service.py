import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.development_history import DevelopmentLog
from app.models.development import DailySummary
from app.models.activity_log import ActivityLog
from app.models.sentiment import BatchSentiment
from app.models.security import GhostLoginAlert
from app.services.gemini_service import GeminiService

class AIPlanningService:
    @staticmethod
    async def generate_strategic_plan(db: Session, lookback_days: int = 15):
        """
        Gathers data from across the system and uses Gemini to generate a 7-day plan.
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(days=lookback_days)
        
        # 1. Fetch Development History
        dev_history = db.query(DevelopmentLog).filter(DevelopmentLog.created_at >= cutoff).all()
        # DevelopmentLog from history has: title, description, batch
        history_desc = "\n".join([f"- [{h.batch or 'General'}] {h.title} ({h.description or ''})" for h in dev_history])
        
        # 2. Fetch Student Activity metrics
        recent_summaries = db.query(DailySummary).order_by(DailySummary.date.desc()).limit(7).all()
        
        # 3. Fetch Critical Unresolved Issues
        security_alerts = db.query(GhostLoginAlert).filter(GhostLoginAlert.is_resolved == False).count()
        
        # 4. Construct AI Prompt
        prompt = f"""
        You are the Eduecosystem Strategic AI Architect. Analyze the recent project status and generate a 7-day development plan.
        
        Recent Development History (last {lookback_days} days):
        {history_desc if history_desc else "No recent logs."}
        
        Current Unresolved Security Alerts: {security_alerts}
        
        Return a JSON object with:
        1. "generated_plan": A list of 7 objects (Day 1-7), each with "day", "date", "portal", "tasks" (list), "priority" (high|medium|low), "estimatedHours".
        2. "strategic_insights": A list of 5 objects with "type" (enhancement|priority|recommendation), "message", "portal".
        
        Make the tasks highly realistic and technical based on the Eduecosystem tech stack (FastAPI, Next.js, Gemini AI).
        Focus on bridging gaps between portals and the next logical evolution of the current features.
        """
        
        try:
            raw_response = await GeminiService.generate_content(prompt)
            # Basic JSON extraction
            if "```json" in raw_response:
                raw_response = raw_response.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_response:
                raw_response = raw_response.split("```")[1].split("```")[0].strip()
                
            data = json.loads(raw_response)
            return data
        except Exception as e:
            print(f"Error generating AI plan: {e}")
            return None

ai_planning_service = AIPlanningService()
