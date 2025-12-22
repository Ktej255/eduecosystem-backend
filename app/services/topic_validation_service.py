"""
Topic Validation Service
Validates that student-submitted content matches the video lesson topic
before generating scores to prevent irrelevant content from receiving scores.
"""

from typing import Dict, Any, Optional
import json
from app.services.ai_service import ai_service


class TopicValidationService:
    """Service for validating topic relevance between student content and video lessons"""

    async def extract_topic_from_content(self, content_text: str) -> Dict[str, Any]:
        """
        Extract the main topic/subject from student content.
        
        Args:
            content_text: The transcribed or OCR'd student content
            
        Returns:
            Dict containing detected_topic, confidence, and keywords
        """
        if not content_text or len(content_text.strip()) < 20:
            return {
                "detected_topic": "Unknown",
                "confidence": 0.0,
                "keywords": [],
                "error": "Content too short to analyze"
            }

        system_message = """You are an expert at identifying topics in educational content.
Analyze the given text and identify the main subject/topic it discusses.
Return ONLY valid JSON with no additional text."""

        prompt = f"""Analyze this student's content and identify the main topic:

CONTENT:
---
{content_text[:3000]}
---

Return JSON:
{{
    "detected_topic": "Main topic (e.g., 'Art and Culture', 'Indian History', 'Economics', 'Polity', 'Environment')",
    "sub_topics": ["Sub-topic 1", "Sub-topic 2"],
    "confidence": 0.0 to 1.0,
    "keywords": ["key", "words", "found"],
    "topic_category": "UPSC GS category if applicable (GS1/GS2/GS3/GS4)",
    "summary": "One line summary of what the content discusses"
}}"""

        try:
            response = await ai_service.generate_text(
                prompt=prompt,
                system_message=system_message,
                max_tokens=500,
                temperature=0.2,
                provider="grok"
            )
            
            # Parse JSON response
            result = json.loads(self._clean_json_response(response))
            return result
            
        except json.JSONDecodeError as e:
            return {
                "detected_topic": "Unknown",
                "confidence": 0.0,
                "keywords": [],
                "error": f"Failed to parse AI response: {str(e)}"
            }
        except Exception as e:
            return {
                "detected_topic": "Unknown",
                "confidence": 0.0,
                "keywords": [],
                "error": str(e)
            }

    async def validate_topic_relevance(
        self,
        video_topic: str,
        video_keywords: list,
        student_content: str,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Validate if student content is relevant to the video topic.
        
        Args:
            video_topic: The topic of the video lesson
            video_keywords: Key terms/concepts from the video
            student_content: The student's submitted content (text)
            threshold: Minimum relevance score (0-1) to consider content relevant
            
        Returns:
            Dict with is_relevant, relevance_score, detected_topic, and reasoning
        """
        # First extract topic from student content
        student_topic_info = await self.extract_topic_from_content(student_content)
        
        if student_topic_info.get("error"):
            return {
                "is_relevant": False,
                "relevance_score": 0.0,
                "detected_topic": "Unknown",
                "expected_topic": video_topic,
                "reasoning": student_topic_info.get("error"),
                "validation_status": "error"
            }

        # Now compare topics
        system_message = """You are an expert at comparing educational topics for relevance.
Determine if the student's content topic matches the expected video topic.
Be strict - unrelated topics should score low. Similar but not exact topics should score medium.
Return ONLY valid JSON."""

        prompt = f"""Compare these topics and determine relevance:

VIDEO LESSON TOPIC: {video_topic}
VIDEO KEY CONCEPTS: {', '.join(video_keywords[:10])}

STUDENT CONTENT TOPIC: {student_topic_info.get('detected_topic', 'Unknown')}
STUDENT KEYWORDS: {', '.join(student_topic_info.get('keywords', [])[:10])}
STUDENT SUMMARY: {student_topic_info.get('summary', 'N/A')}

Analyze if the student's content is relevant to the video lesson topic.

Return JSON:
{{
    "is_relevant": true/false,
    "relevance_score": 0.0 to 1.0,
    "reasoning": "Explanation of why topics match or don't match",
    "match_type": "exact_match / related / partially_related / unrelated",
    "recommendation": "What the student should do if topics don't match"
}}"""

        try:
            response = await ai_service.generate_text(
                prompt=prompt,
                system_message=system_message,
                max_tokens=500,
                temperature=0.2,
                provider="grok"
            )
            
            comparison = json.loads(self._clean_json_response(response))
            
            # Determine final relevance based on score and threshold
            relevance_score = comparison.get("relevance_score", 0.0)
            is_relevant = relevance_score >= threshold
            
            return {
                "is_relevant": is_relevant,
                "relevance_score": relevance_score,
                "detected_topic": student_topic_info.get("detected_topic"),
                "expected_topic": video_topic,
                "match_type": comparison.get("match_type", "unknown"),
                "reasoning": comparison.get("reasoning", ""),
                "recommendation": comparison.get("recommendation", ""),
                "student_keywords": student_topic_info.get("keywords", []),
                "video_keywords": video_keywords[:10],
                "validation_status": "success"
            }
            
        except json.JSONDecodeError as e:
            return {
                "is_relevant": True,  # Default to allowing on parse error
                "relevance_score": 1.0,
                "detected_topic": student_topic_info.get("detected_topic"),
                "expected_topic": video_topic,
                "reasoning": f"Validation skipped due to parse error: {str(e)}",
                "validation_status": "skipped"
            }
        except Exception as e:
            return {
                "is_relevant": True,  # Default to allowing on error
                "relevance_score": 1.0,
                "detected_topic": student_topic_info.get("detected_topic"),
                "expected_topic": video_topic,
                "reasoning": f"Validation skipped due to error: {str(e)}",
                "validation_status": "skipped"
            }

    def _clean_json_response(self, response: str) -> str:
        """Clean markdown formatting from AI JSON response"""
        clean = response.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        return clean.strip()


# Global instance
topic_validation_service = TopicValidationService()
