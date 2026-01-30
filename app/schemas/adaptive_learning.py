from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.adaptive_learning import GranularityType, MasteryStatus

# Shared properties
class ConceptBase(BaseModel):
    title: str
    subject: str
    difficulty_level: Optional[int] = 1
    granularity_type: Optional[GranularityType] = GranularityType.NANO_POINT

class ConceptCreate(ConceptBase):
    pass

class Concept(ConceptBase):
    id: UUID
    
    class Config:
        orm_mode = True

class KnowledgeMapNode(Concept):
    mastery_probability: float = 0.0
    mastery_status: str = "Red"
    is_locked: bool = False

# Dependency Schemas
class DependencyCreate(BaseModel):
    parent_id: UUID
    child_id: UUID
    strength: Optional[float] = 1.0

# Interaction Schemas
class InteractionCreate(BaseModel):
    question_id: Optional[str] = None
    associated_concept_id: UUID
    is_correct: bool
    time_taken_ms: int
    hesitation_detected: bool = False
    backspaces_count: int = 0

class InteractionResponse(BaseModel):
    status: str
    mastery_probability: float
    mastery_status: str
    recommendation: Optional[Dict[str, Any]] = None

# Generation Schemas
class GenerateContentRequest(BaseModel):
    concept_id: UUID
    interaction_context: Optional[Dict[str, Any]] = None

class GeneratedContent(BaseModel):
    question_text: str
    options: List[str]
    correct_option_index: int
    explanation: str
    explanation: str
    strategy_used: Optional[str] = None

# Counseling Schemas
class CounselingRequest(BaseModel):
    concept_id: UUID

class CounselingResponse(BaseModel):
    message: str
    detected_emotion: str
    concept_id: UUID
