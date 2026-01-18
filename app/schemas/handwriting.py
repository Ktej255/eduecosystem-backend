from pydantic import BaseModel
from typing import Optional, List

class HandwritingFeatures(BaseModel):
    baseline: Optional[str] = None
    slant: Optional[str] = None
    pressure: Optional[str] = None
    size: Optional[str] = None
    spacing: Optional[str] = None
    confidence_score: float = 0.0
    personality_traits: List[str] = []
    error: Optional[str] = None

class HandwritingAnalysis(BaseModel):
    extracted_text: str
    features: HandwritingFeatures
    analysis: str
