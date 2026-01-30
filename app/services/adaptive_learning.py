from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.adaptive_learning import (
    Concept,
    ConceptDependency,
    StudentMastery,
    InteractionLog,
    MasteryStatus,
)
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

class AdaptiveLearningService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_mastery(self, user_id: int, concept_id: UUID) -> Optional[StudentMastery]:
        return (
            self.db.query(StudentMastery)
            .filter(StudentMastery.user_id == user_id, StudentMastery.concept_id == concept_id)
            .first()
        )

    def log_interaction(self, user_id: int, interaction_data: Dict[str, Any]) -> InteractionLog:
        """
        Logs an interaction and triggers the BKT update.
        """
        db_log = InteractionLog(
            user_id=user_id,
            question_id=interaction_data.get("question_id"),
            associated_concept_id=interaction_data.get("associated_concept_id"),
            is_correct=interaction_data.get("is_correct"),
            time_taken_ms=interaction_data.get("time_taken_ms"),
            hesitation_detected=interaction_data.get("hesitation_detected"),
            backspaces_count=interaction_data.get("backspaces_count"),
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)

        # Trigger BKT Update
        if db_log.associated_concept_id:
            self.update_mastery(user_id, db_log.associated_concept_id, db_log)

        return db_log

    def update_mastery(
        self, user_id: int, concept_id: UUID, interaction: InteractionLog
    ) -> StudentMastery:
        """
        Bayesian Knowledge Tracing (BKT) Update Logic.
        """
        mastery = self.get_user_mastery(user_id, concept_id)
        if not mastery:
            print("DEBUG: Creating NEW mastery record (0.3)")
            mastery = StudentMastery(
                user_id=user_id,
                concept_id=concept_id,
                mastery_probability=0.3,
                status=MasteryStatus.RED,
                confidence_score=0.5
            )
            self.db.add(mastery)
        else:
            print(f"DEBUG: Found existing mastery: {mastery.mastery_probability}")

        # BKT Parameters
        p_known = mastery.mastery_probability
        p_guess = 0.2
        p_slip = 0.1
        p_transit = 0.1

        if interaction.hesitation_detected:
            p_guess = 0.4
            
        print(f"DEBUG: p_known={p_known}, correct={interaction.is_correct}")

        if interaction.is_correct:
            numerator = p_known * (1 - p_slip)
            denominator = numerator + (1 - p_known) * p_guess
            p_known_given_obs = numerator / denominator
        else:
            numerator = p_known * p_slip
            denominator = numerator + (1 - p_known) * (1 - p_guess)
            p_known_given_obs = numerator / denominator

        p_new = p_known_given_obs + (1 - p_known_given_obs) * p_transit
        p_new = max(0.0, min(1.0, p_new))
        
        print(f"DEBUG: p_new={p_new}")

        mastery.mastery_probability = p_new
        mastery.last_assessed_at = datetime.utcnow()
        
        if p_new < 0.5:
            mastery.status = MasteryStatus.RED
        elif p_new < 0.8:
            mastery.status = MasteryStatus.YELLOW
        else:
            mastery.status = MasteryStatus.GREEN

        self.db.add(mastery) # Ensure added/updated
        self.db.commit()
        self.db.refresh(mastery)
        
        return mastery

    def get_knowledge_map(self, user_id: int) -> Dict[str, Any]:
        """
        Returns the graph: Nodes (Concepts + Mastery + Lock Status) and Edges (Dependencies).
        """
        # 1. Fetch all concepts and dependencies
        concepts = self.db.query(Concept).all()
        dependencies = self.db.query(ConceptDependency).all()
        
        # 2. Fetch user's mastery states
        mastery_entries = (
            self.db.query(StudentMastery)
            .filter(StudentMastery.user_id == user_id)
            .all()
        )
        mastery_map = {m.concept_id: m for m in mastery_entries}
        
        # 3. Build Adjacency List for Parents (Child -> [Parents])
        parents_map = {}
        for dep in dependencies:
            if dep.child_concept_id not in parents_map:
                parents_map[dep.child_concept_id] = []
            parents_map[dep.child_concept_id].append(dep.parent_concept_id)

        # 4. Construct Nodes with Status
        nodes = []
        for concept in concepts:
            mastery = mastery_map.get(concept.id)
            
            # Locking Logic
            is_locked = False
            parents = parents_map.get(concept.id, [])
            if parents:
                # Check if ALL parents are "Unlocked" enough (allow Yellow/Green)
                # Strict: Parent must be > 0.5 (Yellow or Green) to unlock child.
                for parent_id in parents:
                    parent_mastery = mastery_map.get(parent_id)
                    if not parent_mastery or parent_mastery.mastery_probability < 0.5:
                        is_locked = True
                        break
            
            nodes.append({
                "id": concept.id,
                "label": concept.title,
                "title": concept.title, # Added for schema compatibility
                "subject": concept.subject, # Added for schema compatibility
                "difficulty_level": concept.difficulty_level, # Added
                "granularity_type": concept.granularity_type, # Added
                "mastery_probability": mastery.mastery_probability if mastery else 0.0,
                "mastery_status": mastery.status if mastery else MasteryStatus.RED,
                "is_locked": is_locked
            })
            
        # 5. Construct Edges
        edges = [
            {
                "source": dep.parent_concept_id,
                "target": dep.child_concept_id,
                "strength": dep.strength
            }
            for dep in dependencies
        ]
        
        return {"nodes": nodes, "edges": edges}
