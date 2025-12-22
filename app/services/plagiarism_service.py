"""
Plagiarism Detection Service

Detect plagiarism using text similarity and web search.
"""

import openai
import os
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from difflib import SequenceMatcher

from app.models.ai_features import PlagiarismCheck
from app.models.assignment import Submission

logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")


class PlagiarismService:
    """
    Detect plagiarism in student submissions.
    """

    @staticmethod
    async def check_plagiarism(
        db: Session,
        submission_id: int,
        text: str,
        assignment_id: int,
        student_id: int,
        threshold: float = 25.0,
        user_id: int = None,
    ) -> PlagiarismCheck:
        """
        Check submission for plagiarism.

        Args:
            db: Database session
            submission_id: ID of the submission
            text: Submission text to check
            assignment_id: ID of the assignment
            student_id: ID of the student
            threshold: Similarity threshold for plagiarism flag
            user_id: ID of the user requesting check

        Returns:
            PlagiarismCheck with similarity scores and matches
        """
        try:
            # Check against other submissions in the same assignment
            peer_matches = PlagiarismService._check_peer_submissions(
                db, text, assignment_id, student_id
            )

            # Check for AI-generated content indicators
            ai_score = await PlagiarismService._check_ai_generation(text)

            # Combine results
            all_matches = peer_matches

            # Calculate overall similarity
            max_similarity = max([m["percentage"] for m in all_matches], default=0)
            originality_score = 100 - max_similarity

            # Determine if plagiarized
            is_plagiarized = max_similarity >= threshold
            review_required = (
                max_similarity >= 15 or ai_score > 0.7
            )  # Flag for review if close

            # Create plagiarism check
            check = PlagiarismCheck(
                submission_id=submission_id,
                assignment_id=assignment_id,
                student_id=student_id,
                similarity_percentage=max_similarity,
                originality_score=originality_score,
                matches=all_matches,
                is_plagiarized=is_plagiarized,
                review_required=review_required,
                check_method="ai",
            )
            db.add(check)
            db.commit()
            db.refresh(check)

            logger.info(f"Plagiarism check complete. Similarity: {max_similarity}%")
            return check

        except Exception as e:
            logger.error(f"Plagiarism check failed: {str(e)}")
            raise

    @staticmethod
    def _check_peer_submissions(
        db: Session, text: str, assignment_id: int, student_id: int
    ) -> List[Dict]:
        """
        Check similarity against other student submissions.
        """
        matches = []

        # Get other submissions for this assignment
        other_submissions = (
            db.query(Submission)
            .filter(
                Submission.assignment_id == assignment_id,
                Submission.user_id != student_id,
            )
            .all()
        )

        for submission in other_submissions:
            if submission.content:
                similarity = PlagiarismService._calculate_similarity(
                    text, submission.content
                )

                if similarity > 10:  # Only record significant matches
                    matches.append(
                        {
                            "source": f"Student submission #{submission.id}",
                            "url": None,
                            "percentage": round(similarity, 2),
                            "text_snippet": submission.content[:200],
                            "matched_phrases": [],  # Could extract specific matches
                        }
                    )

        return sorted(matches, key=lambda x: x["percentage"], reverse=True)[:5]

    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """
        Calculate text similarity using SequenceMatcher.
        """
        # Normalize texts
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()

        # Calculate similarity
        similarity = SequenceMatcher(None, text1, text2).ratio()

        return similarity * 100

    @staticmethod
    async def _check_ai_generation(text: str) -> float:
        """
        Check if text appears to be AI-generated.
        Returns score 0-1, where 1 is highly likely AI-generated.
        """
        try:
            # Use GPT to detect AI patterns
            prompt = f"""Analyze the following text and determine if it appears to be AI-generated.
Look for patterns like:
- Overly formal or perfect grammar
- Lack of personal voice
- Repetitive sentence structures
- Generic statements

Text:
{text[:1000]}

Respond with just a score from 0 to 1, where:
0 = Definitely human-written
1 = Definitely AI-generated

Score:"""

            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=10,
            )

            # Extract score
            score_text = response.choices[0].message.content.strip()
            try:
                score = float(score_text)
                return max(0, min(1, score))
            except ValueError:
                return 0.0

        except Exception as e:
            logger.warning(f"AI detection check failed: {e}")
            return 0.0

    @staticmethod
    def get_plagiarism_check(
        db: Session, submission_id: int
    ) -> Optional[PlagiarismCheck]:
        """
        Retrieve plagiarism check for a submission.
        """
        return (
            db.query(PlagiarismCheck)
            .filter(PlagiarismCheck.submission_id == submission_id)
            .first()
        )

    @staticmethod
    def review_plagiarism_check(db: Session, check_id: int, instructor_notes: str):
        """
        Mark plagiarism check as reviewed by instructor.
        """
        check = db.query(PlagiarismCheck).filter(PlagiarismCheck.id == check_id).first()

        if check:
            check.reviewed_by_instructor = True
            check.instructor_notes = instructor_notes
            db.commit()
