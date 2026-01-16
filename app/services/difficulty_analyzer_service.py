"""
Difficulty Analyzer Service

Analyze content difficulty using readability metrics and AI.
"""

import os
import logging
import re
from typing import Dict
from sqlalchemy.orm import Session

from app.models.ai_features import ContentDifficultyAnalysis

logger = logging.getLogger(__name__)

from app.services.gemini_service import gemini_service
# openai.api_key = os.getenv("OPENAI_API_KEY")


class DifficultyAnalyzerService:
    """
    Analyze content difficulty and readability.
    """

    @staticmethod
    def analyze_difficulty(
        db: Session,
        content_id: int,
        content_type: str,
        content_text: str,
        target_level: str = "undergraduate",
        user_id: int = None,
    ) -> ContentDifficultyAnalysis:
        """
        Analyze content difficulty.

        Args:
            db: Database session
            content_id: ID of the content
            content_type: 'course' or 'lesson'
            content_text: The content to analyze
            target_level: Target audience level
            user_id: ID of the user requesting analysis

        Returns:
            ContentDifficultyAnalysis with metrics and suggestions
        """
        try:
            # Calculate readability scores
            metrics = DifficultyAnalyzerService._calculate_readability(content_text)

            # Get AI analysis for suggestions
            ai_suggestions = DifficultyAnalyzerService._get_ai_suggestions(
                content_text, target_level, metrics
            )

            # Determine recommended level
            recommended_level = DifficultyAnalyzerService._determine_level(metrics)

            # Create analysis
            analysis = ContentDifficultyAnalysis(
                content_id=content_id,
                content_type=content_type,
                flesch_reading_ease=metrics["flesch_reading_ease"],
                flesch_kincaid_grade=metrics["flesch_kincaid_grade"],
                gunning_fog_index=metrics.get("gunning_fog", 0),
                smog_index=metrics.get("smog", 0),
                avg_sentence_length=metrics["avg_sentence_length"],
                avg_word_length=metrics["avg_word_length"],
                vocabulary_complexity=metrics["vocabulary_complexity"],
                concept_density=metrics.get("concept_density", 50),
                recommended_level=recommended_level,
                target_audience=DifficultyAnalyzerService._get_audience(
                    recommended_level
                ),
                estimated_reading_time=metrics["reading_time"],
                simplification_suggestions=ai_suggestions.get("suggestions", []),
                difficult_terms=ai_suggestions.get("difficult_terms", []),
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)

            logger.info(f"Content difficulty analyzed. Level: {recommended_level}")
            return analysis

        except Exception as e:
            logger.error(f"Difficulty analysis failed: {str(e)}")
            raise

    @staticmethod
    def _calculate_readability(text: str) -> Dict:
        """
        Calculate various readability metrics.
        """
        # Clean text
        text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
        text = re.sub(r"\s+", " ", text).strip()

        # Count sentences, words, syllables
        sentences = re.split(r"[.!?]+", text)
        sentences = [s for s in sentences if s.strip()]
        num_sentences = len(sentences)

        words = text.split()
        num_words = len(words)

        num_syllables = sum(
            [DifficultyAnalyzerService._count_syllables(word) for word in words]
        )

        # Avoid division by zero
        if num_sentences == 0 or num_words == 0:
            return {
                "flesch_reading_ease": 100,
                "flesch_kincaid_grade": 0,
                "avg_sentence_length": 0,
                "avg_word_length": 0,
                "vocabulary_complexity": 0,
                "reading_time": 0,
            }

        # Flesch Reading Ease: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        flesch = (
            206.835
            - 1.015 * (num_words / num_sentences)
            - 84.6 * (num_syllables / num_words)
        )
        flesch = max(0, min(100, flesch))  # Clamp to 0-100

        # Flesch-Kincaid Grade Level: 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        fk_grade = (
            0.39 * (num_words / num_sentences)
            + 11.8 * (num_syllables / num_words)
            - 15.59
        )
        fk_grade = max(0, fk_grade)

        # Average sentence length
        avg_sentence_len = num_words / num_sentences

        # Average word length
        avg_word_len = sum([len(w) for w in words]) / num_words

        # Vocabulary complexity (% of words > 6 chars)
        complex_words = [w for w in words if len(w) > 6]
        vocab_complexity = (len(complex_words) / num_words) * 100

        # Reading time (avg 200 words per minute)
        reading_time = round(num_words / 200)

        return {
            "flesch_reading_ease": round(flesch, 2),
            "flesch_kincaid_grade": round(fk_grade, 2),
            "avg_sentence_length": round(avg_sentence_len, 2),
            "avg_word_length": round(avg_word_len, 2),
            "vocabulary_complexity": round(vocab_complexity, 2),
            "reading_time": max(1, reading_time),
        }

    @staticmethod
    def _count_syllables(word: str) -> int:
        """
        Estimate syllable count for a word.
        """
        word = word.lower()
        vowels = "aeiouy"
        syllables = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllables += 1
            previous_was_vowel = is_vowel

        # Adjust for silent 'e'
        if word.endswith("e"):
            syllables -= 1

        # Minimum 1 syllable
        return max(1, syllables)

    @staticmethod
    def _get_ai_suggestions(text: str, target_level: str, metrics: Dict) -> Dict:
        """
        Get AI-powered simplification suggestions using Gemini.
        """
        try:
            prompt = f"""
            Analyze this text for difficulty and provide simplification suggestions.
            Target Audience: {target_level}
            Readability Metrics: {metrics}
            Text Sample: "{text[:1000]}..."

            Return JSON with two keys:
            1. "suggestions": List of 3-5 specific actionable suggestions to improve clarity for the target audience.
            2. "difficult_terms": List of complex or jargon words found in the text that should be defined or simplified.
            """
            
            response = gemini_service.generate_text(prompt, temperature=0.3, json_mode=True)
            import json
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            return {
                "suggestions": data.get("suggestions", []),
                "difficult_terms": data.get("difficult_terms", [])
            }
        except Exception as e:
            logger.error(f"AI Suggestion Error: {e}")
            # Minimal fallback if AI fails entirely
            return {
                "suggestions": ["Could not generate specific AI suggestions at this time."],
                "difficult_terms": []
            }

    @staticmethod
    def _determine_level(metrics: Dict) -> str:
        """
        Determine recommended level based on metrics.
        """
        fk_grade = metrics["flesch_kincaid_grade"]

        if fk_grade < 6:
            return "beginner"
        elif fk_grade < 10:
            return "intermediate"
        else:
            return "advanced"

    @staticmethod
    def _get_audience(level: str) -> str:
        """
        Map level to target audience.
        """
        mapping = {
            "beginner": "High school students",
            "intermediate": "Undergraduate students",
            "advanced": "Graduate students & professionals",
        }
        return mapping.get(level, "General audience")
