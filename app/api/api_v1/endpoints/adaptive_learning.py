from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.services.adaptive_learning import AdaptiveLearningService
from app.services.adaptive_content_service import AdaptiveContentService
from app.models.adaptive_learning import Concept as ConceptModel, ConceptDependency, GranularityType
from app.schemas.adaptive_learning import (
    ConceptCreate, 
    Concept, 
    DependencyCreate, 
    InteractionCreate, 
    InteractionResponse,
    GenerateContentRequest,
    GeneratedContent,
    CounselingRequest,
    CounselingResponse
)
from app.services.adaptive_counseling_service import AdaptiveCounselingService

router = APIRouter()

# ... existing endpoints ...

@router.post("/counsel", response_model=CounselingResponse)
def get_counseling_message(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    request: CounselingRequest
) -> Any:
    """
    Get an AI counseling message based on recent interactions.
    """
    service = AdaptiveCounselingService(db)
    try:
        response = service.generate_counseling_message(current_user.id, request.concept_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/concepts", response_model=Concept)
def create_concept(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    concept_in: ConceptCreate
) -> Any:
    """
    Create a new knowledge concept (Node).
    Only admin or teachers should likely do this, but keeping open for now.
    """
    if not current_user.is_superuser: # Basic guard
        raise HTTPException(status_code=403, detail="Not authorized")
        
    concept = ConceptModel(
        title=concept_in.title,
        subject=concept_in.subject,
        difficulty_level=concept_in.difficulty_level,
        granularity_type=concept_in.granularity_type
    )
    db.add(concept)
    db.commit()
    db.refresh(concept)
    return concept

@router.post("/dependencies", response_model=Dict[str, Any])
def create_dependency(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    dep_in: DependencyCreate
) -> Any:
    """
    Create a dependency between two concepts (Edge).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    dep = ConceptDependency(
        parent_concept_id=dep_in.parent_id,
        child_concept_id=dep_in.child_id,
        strength=dep_in.strength
    )
    db.add(dep)
    db.commit()
    return {"status": "created", "parent": dep_in.parent_id, "child": dep_in.child_id}

@router.get("/knowledge-map", response_model=Dict[str, Any])
def get_knowledge_map(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get the full knowledge graph with user's mastery status.
    """
    service = AdaptiveLearningService(db)
    return service.get_knowledge_map(current_user.id)

@router.post("/interaction", response_model=InteractionResponse)
def log_interaction(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    interaction_in: InteractionCreate
) -> Any:
    """
    Log a student interaction (answer attempt) and update BKT.
    """
    service = AdaptiveLearningService(db)
    
    # Dump model to dict for service compatibility
    data = interaction_in.dict()
    data["associated_concept_id"] = str(data["associated_concept_id"]) # Ensure UUID handled if service expects str or UUID
        
    try:
        log = service.log_interaction(current_user.id, data)
        # Get updated mastery to return
        updated_mastery = service.get_user_mastery(current_user.id, interaction_in.associated_concept_id)
        
        recommendation = None
        # Diagnostic Trigger: If incorrect and mastery is low, check parents
        if not data.get("is_correct", False) and getattr(updated_mastery, 'status', 'Red') == "Red":
            # Check parents
            parents = service.db.query(ConceptDependency).filter(
                ConceptDependency.child_concept_id == interaction_in.associated_concept_id
            ).all()
            
            for dep in parents:
                parent_mastery = service.get_user_mastery(current_user.id, dep.parent_concept_id)
                # If parent is not Green (Mastered), flag it
                if not parent_mastery or parent_mastery.status != "Green":
                    recommendation = {
                        "type": "review_prerequisite",
                        "concept_id": str(dep.parent_concept_id),
                        "message": "It seems you are struggling. We recommend reviewing the prerequisite concept."
                    }
                    break # Just one for now
        
        return {
            "status": "logged", 
            "mastery_probability": updated_mastery.mastery_probability if updated_mastery else 0.0,
            "mastery_status": updated_mastery.status if updated_mastery else "Red",
            "recommendation": recommendation
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/generate", response_model=GeneratedContent)
def generate_content(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    request: GenerateContentRequest
) -> Any:
    """
    Generate remedial/adaptive content based on student's state.
    """
    service = AdaptiveContentService(db)
    try:
        content = service.generate_remedial_content(
            current_user.id, 
            request.concept_id, 
            request.interaction_context
        )
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
