from sqlalchemy.orm import Session
from app.models.adaptive_learning import InteractionLog, Concept, StudentMastery
from app.services.gemini_service import GeminiService
from typing import List, Optional, Dict, Any
from uuid import UUID
import random
from datetime import datetime, timedelta

class AdaptiveCounselingService:
    def __init__(self, db: Session):
        self.db = db
        self.gemini_service = GeminiService()

    def analyze_sentiment(self, user_id: int, recent_interactions: List[InteractionLog]) -> str:
        """
        Analyze recent interactions to detect emotional state.
        Heuristics:
        - High hesitancy + Incorrect answers = Frustration
        - Incorrect answers + Fast time = Guessing / Impatience
        - Correct + Fast = Flow / Confidence
        - Correct + High hesitancy = Uncertainty
        """
        if not recent_interactions:
            return "neutral"

        hesitation_count = sum(1 for i in recent_interactions if i.hesitation_detected)
        incorrect_count = sum(1 for i in recent_interactions if not i.is_correct)
        avg_time = sum(i.time_taken_ms for i in recent_interactions) / len(recent_interactions)

        # Thresholds (Simulated)
        if incorrect_count >= 2 and hesitation_count >= 1:
            return "frustration"
        elif incorrect_count >= 2 and avg_time < 3000: # Very fast failures
            return "impatience"
        elif incorrect_count == 0:
            return "confidence"
        
        return "neutral"

    def generate_counseling_message(self, user_id: int, concept_id: UUID) -> Dict[str, Any]:
        """
        Generate a personalized counseling message based on recent context.
        """
        # 1. Fetch Context
        concept = self.db.query(Concept).filter(Concept.id == concept_id).first()
        # Get last 5 interactions for this concept
        recent_logs = (
            self.db.query(InteractionLog)
            .filter(InteractionLog.user_id == user_id, InteractionLog.associated_concept_id == concept_id)
            .order_by(InteractionLog.created_at.desc())
            .limit(5)
            .all()
        )
        
        emotion = self.analyze_sentiment(user_id, recent_logs)
        
        # 2. Construct Prompt for Gemini
        prompt = f"""
        You are an empathetic AI tutor. The student is learning the concept '{concept.title if concept else "Unknown"}'.
        Based on their recent activity, their detected emotional state is: {emotion}.
        
        Context details:
        - Subject: {concept.subject if concept else "General"}
        - Recent accuracy: {sum(1 for i in recent_logs if i.is_correct)}/{len(recent_logs)} correct.
        
        Generate a short, encouraging message (max 2 sentences).
        If confirmed frustration, offer a break or specific encouragement.
        If confidence, celebrate their progress.
        If neutral, just offer support.
        
        Return ONLY the message text.
        """
        
        # 3. Call LLM
        # Using a dummy user object for premium check if needed, or passing None if service supports it
        # Assuming generate_text handles User objects. We'll pass a mock or current user if available in logic.
        # For now, we will use a simplified call or assume GeminiService handles auth.
        
        # NOTE: In a real scenario, we'd pass the user object. 
        # For simplicity here, we assume the valid API key is enough.
        
        try:
             # We need a user object for generate_text protocol usually, 
             # but we can look up the user or just mock it if strict type checking isn't enforced on the object.
             # Better: Use the service properly.
             # Actually, GeminiService.generate_text requires a `user` object for checking `is_premium`.
             # We will fetch the user.
            from app.models.user import User
            user_obj = self.db.query(User).filter(User.id == user_id).first()
            
            message = self.gemini_service.generate_text(prompt, user=user_obj)
            # Cleanup quotes if any
            message = message.strip('"')
            
        except Exception as e:
            # Fallback if LLM fails
            print(f"LLM Error: {e}")
            if emotion == "frustration":
                message = "It looks like this is a tough one. Take a deep breath, you're doing great!"
            elif emotion == "confidence":
                message = "You are doing amazing! Keep it up!"
            else:
                message = "I'm here to help if you need me."

        return {
            "message": message,
            "detected_emotion": emotion,
            "concept_id": str(concept_id)
        }
