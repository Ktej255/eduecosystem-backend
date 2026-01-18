from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.sentiment import BatchSentiment
from app.models.mood import MoodEntry
from app.services.gemini_service import GeminiService
import json

class SentimentService:
    @staticmethod
    async def aggregate_daily_sentiment(db: Session, batch_name: str, target_date: date = None):
        """
        Aggregates individual moods/reflections into a daily batch sentiment.
        """
        if not target_date:
            target_date = datetime.utcnow().date()
            
        # 1. Fetch all reflection notes for this batch on this date
        # Note: In a real system, we'd join with a 'Batch' table. 
        # For now, we'll assume a generic aggregation or filter by user roles if needed.
        # This is a simplified version.
        
        entries = db.query(MoodEntry).filter(
            func.date(MoodEntry.timestamp) == target_date
        ).all()
        
        if not entries:
            return None
            
        combined_text = " ".join([e.note for e in entries if e.note])
        if not combined_text:
            return None
            
        # 2. Use Gemini to analyze the collective vibe
        prompt = f"""
        Analyze the following collective reflections from a student batch and provide a JSON report.
        Reflections: {combined_text}
        
        Return exactly this JSON format:
        {{
          "focused_score": 0.0-1.0,
          "anxious_score": 0.0-1.0,
          "tired_score": 0.0-1.0,
          "inspired_score": 0.0-1.0,
          "dominant_vibe": "Focused|Anxious|Tired|Inspired",
          "top_keywords": ["keyword1", "keyword2"]
        }}
        """
        
        try:
            analysis_raw = await GeminiService.generate_content(prompt)
            # Basic JSON extraction (Gemini sometimes adds markdown blocks)
            if "```json" in analysis_raw:
                analysis_raw = analysis_raw.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis_raw:
                analysis_raw = analysis_raw.split("```")[1].split("```")[0].strip()
                
            analysis = json.loads(analysis_raw)
            
            # 3. Save to database
            sentiment = db.query(BatchSentiment).filter(
                BatchSentiment.batch_name == batch_name,
                BatchSentiment.date == target_date
            ).first()
            
            if not sentiment:
                sentiment = BatchSentiment(
                    batch_name=batch_name,
                    date=target_date
                )
                db.add(sentiment)
                
            sentiment.focused_score = analysis.get("focused_score", 0.0)
            sentiment.anxious_score = analysis.get("anxious_score", 0.0)
            sentiment.tired_score = analysis.get("tired_score", 0.0)
            sentiment.inspired_score = analysis.get("inspired_score", 0.0)
            sentiment.dominant_vibe = analysis.get("dominant_vibe", "Stable")
            sentiment.top_keywords = ",".join(analysis.get("top_keywords", []))
            sentiment.sample_size = len(entries)
            
            db.commit()
            db.refresh(sentiment)
            return sentiment
            
        except Exception as e:
            print(f"Error aggregating sentiment: {e}")
            return None

    @staticmethod
    def get_sentiment_trends(db: Session, batch_name: str, days: int = 7):
        """Returns sentiment history for trend charts"""
        return db.query(BatchSentiment).filter(
            BatchSentiment.batch_name == batch_name
        ).order_by(BatchSentiment.date.desc()).limit(days).all()

sentiment_service = SentimentService()
