from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from uuid import UUID
import json

from app.services.gemini_service import gemini_service
from app.models.adaptive_learning import Concept, StudentMastery, MasteryStatus

class AdaptiveContentService:
    def __init__(self, db: Session):
        self.db = db

    def generate_remedial_content(
        self, 
        user_id: int, 
        concept_id: UUID, 
        interaction_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates targeted content based on student's mastery state and recent behavior.
        """
        concept = self.db.query(Concept).filter(Concept.id == concept_id).first()
        if not concept:
            raise ValueError("Concept not found")

        mastery = (
            self.db.query(StudentMastery)
            .filter(StudentMastery.user_id == user_id, StudentMastery.concept_id == concept_id)
            .first()
        )
        
        current_status = mastery.status if mastery else MasteryStatus.RED
        current_prob = mastery.mastery_probability if mastery else 0.0
        
        # Determine Strategy based on Signals
        strategy = "standard"
        hesitation = interaction_context.get("hesitation_detected", False) if interaction_context else False
        last_was_incorrect = not interaction_context.get("is_correct", True) if interaction_context else False
        
        if current_status == MasteryStatus.RED:
            if hesitation:
                strategy = "scaffolding" # Break it down
            elif last_was_incorrect:
                strategy = "remedial_with_hint" # Explain the misconception
            else:
                strategy = "foundational" # Teach from scratch
        elif current_status == MasteryStatus.YELLOW:
            strategy = "diagnostic_micro_test" # Check edge cases
        else: # GREEN
            strategy = "challenge" # Advanced application
            
        # Construct Prompt
        prompt = self._construct_prompt(concept, strategy, interaction_context)
        
        # Call AI
        response_text = gemini_service.generate_text(
            prompt=prompt, 
            temperature=0.7, 
            max_tokens=1000
        )
        
        # Parse output
        try:
            # Basic cleanup if Markdown is returned
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            content = json.loads(clean_text)
            content["strategy_used"] = strategy
            return content
        except Exception as e:
            return {
                "error": "Failed to parse AI response", 
                "raw_response": response_text,
                "strategy_used": strategy
            }

    def _construct_prompt(self, concept: Concept, strategy: str, context: Optional[Dict[str, Any]]) -> str:
        base_instruction = f"""
        You are an expert educational AI tutor.
        Topic: {concept.title} ({concept.subject})
        Difficulty: {concept.difficulty_level}/10
        Target Audience: Student learning this concept.
        
        Generate a single multiple-choice question (MCQ) in JSON format.
        Format:
        {{
            "question_text": "...",
            "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "correct_option_index": 0,
            "explanation": "..."
        }}
        """
        
        strategy_instruction = ""
        if strategy == "scaffolding":
            strategy_instruction = """
            The student is hesitating. This suggests cognitive load is too high.
            Create a "Scaffolding Question" that simplifies the problem. 
            Break the concept down into a smaller, easier step.
            In the explanation, explicitly guide them on the thought process.
            """
            
        elif strategy == "remedial_with_hint":
            strategy_instruction = """
            The student just made a mistake.
            Create a variation of the same concept but provide a subtle HINT in the question text.
            Focus on correcting common misconceptions related to this topic.
            """
            
        elif strategy == "diagnostic_micro_test":
            strategy_instruction = """
            The student is borderline (Yellow).
            Create a "Diagnostic Micro-Test". 
            This question should test a specific nuance or corner case to definitively verify mastery.
            Make distractor options (wrong answers) represent specific common logical errors.
            """
            
        elif strategy == "challenge":
            strategy_instruction = """
            The student has mastered this (Green).
            Create a "Challenge Question".
            Combine this concept with a real-world application or a cross-domain problem.
            """
            
        else: # Foundational
            strategy_instruction = """
            The student is struggling (Red).
            Create a "Foundational Question".
            Test the most basic definition or property of this concept.
            Keep the language simple and direct.
            """
            
        return f"{base_instruction}\n\nSTRATEGY: {strategy}\n{strategy_instruction}\n\nJSON ONLY."
