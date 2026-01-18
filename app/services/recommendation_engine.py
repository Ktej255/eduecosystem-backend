from sqlalchemy.orm import Session
from app.models.drill import DrillResult
from typing import Dict, Any, Optional
import random

class RecommendationEngine:
    def generate_smart_offer(self, db: Session, student_id: int) -> Optional[Dict[str, Any]]:
        """
        Analyzes student performance and returns a targeted offer if applicable.
        """
        # 1. Identify Weakest Topic (based on last 10 drills)
        recent_results = db.query(DrillResult).filter(
            DrillResult.user_id == student_id
        ).order_by(DrillResult.completed_at.desc()).limit(10).all()

        if not recent_results:
            return None

        topic_scores = {}
        topic_counts = {}

        for r in recent_results:
            # Assuming 'details' holds topic info or we deduce from drill_id relationship
            # For this mock implementation, we'll simulate topics if not present
            topic = r.details.get("topic", "General") if r.details else "General"
            
            topic_scores[topic] = topic_scores.get(topic, 0) + r.score
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        weakest_topic = None
        min_avg = 101

        for topic, total_score in topic_scores.items():
            avg = total_score / topic_counts[topic]
            if avg < 50 and avg < min_avg:
                min_avg = avg
                weakest_topic = topic

        # 2. Map Topic to Product
        # In a real app, this would query a Product/Bundle table
        PRODUCT_MAP = {
            "Polity": {
                "title": "Polity Mastery Bundle",
                "description": "Crush your fears of the Constitution. Includes 500+ MCQs & Video Lectures.",
                "original_price": 4999,
                "discounted_price": 2499,
                "image_url": "/images/bundles/polity.jpg"
            },
            "History": {
                "title": "History Timestamp",
                "description": "Never forget a date again. Complete visual timeline course.",
                "original_price": 3999,
                "discounted_price": 1999,
                "image_url": "/images/bundles/history.jpg"
            },
            "General": {
                 "title": "Exam Cracker Ultimate",
                 "description": "Boost your overall score by 20% in 30 days.",
                 "original_price": 9999,
                 "discounted_price": 4999,
                 "image_url": "/images/bundles/general.jpg"
            }
        }

        if weakest_topic or min_avg < 60:
             # Default to general if overall average is low but no specific topic is < 50
             # Or strict mapping
             offer_product = PRODUCT_MAP.get(weakest_topic, PRODUCT_MAP["General"])
             
             return {
                 "id": f"offer_{random.randint(1000, 9999)}",
                 "type": "smart_bundle",
                 "reason": f"We noticed you're struggling with {weakest_topic or 'your scores'}. Let's fix that.",
                 "product": offer_product,
                 "expires_in_seconds": 3600 * 24, # 24 hours
                 "discount_code": "SMART50"
             }
        
        return None

recommendation_engine = RecommendationEngine()
