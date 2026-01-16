from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


from app.models.graphotherapy import GRAPHOTHERAPY_LEVELS


class DayCompletionBase(BaseModel):
    level: int
    day_number: int
    notes: Optional[str] = None


class DayCompletionCreate(DayCompletionBase):
    pass


class DayCompletionResponse(DayCompletionBase):
    id: int
    progress_id: int
    completed_at: datetime
    upload_url: Optional[str] = None
    upload_filename: Optional[str] = None

    class Config:
        from_attributes = True


class GraphotherapyProgressBase(BaseModel):
    current_level: int = 1
    current_day: int = 1
    total_streak: int = 0


class GraphotherapyProgressCreate(GraphotherapyProgressBase):
    user_id: int


class GraphotherapyProgressResponse(GraphotherapyProgressBase):
    id: int
    user_id: int
    last_practice_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    day_completions: List[DayCompletionResponse] = []

    class Config:
        from_attributes = True


class LevelInfo(BaseModel):
    level: int
    name: str
    description: str
    total_days: int
    completed_days: int
    is_unlocked: bool
    is_current: bool
    is_completed: bool


class LevelDetailResponse(BaseModel):
    level: int
    name: str
    description: str
    total_days: int
    days: List[dict]  # List of day status objects


class DayDetailResponse(BaseModel):
    level: int
    day_number: int
    is_unlocked: bool
    is_completed: bool
    completed_at: Optional[datetime] = None
    upload_url: Optional[str] = None
    can_complete_today: bool


class DayCompleteRequest(BaseModel):
    notes: Optional[str] = None


class DayCompleteResponse(BaseModel):
    success: bool
    message: str
    upload_url: Optional[str] = None
    new_streak: int
    level_completed: bool = False
    next_level_unlocked: bool = False


class OverviewResponse(BaseModel):
    current_level: int
    current_day: int
    total_streak: int
    last_practice_date: Optional[datetime] = None
    levels: List[LevelInfo]

# --- V2 Schemas for Admin Portal ---

class GraphoBookBase(BaseModel):
    title: str
    level: int
    total_days: int = 30
    is_published: bool = False

class GraphoBookCreate(GraphoBookBase):
    pass

class GraphoBookResponse(GraphoBookBase):
    id: int
    pdf_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class GraphoPageBase(BaseModel):
    day: int
    page_number: int
    
class GraphoPageCreate(GraphoPageBase):
    pass

class GraphoPageResponse(GraphoPageBase):
    id: int
    book_id: int
    reference_image_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class GraphoSubmissionResponse(BaseModel):
    id: int
    user_id: int
    day: int
    image_url: str
    status: str
    verification_score: Optional[int] = None
    started_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    completed_at: datetime
    
    class Config:
        from_attributes = True


# --- Phase 4: Transformation & Prediction Schemas ---

class TransformationComparisonRequest(BaseModel):
    user_id: Optional[int] = None
    baseline_day: int = 1
    current_day: int = 21

class ComparisonMetric(BaseModel):
    name: str # e.g. "Slant Stability"
    baseline_value: float # 0-100
    current_value: float # 0-100
    change_percentage: float
    status: str # "Improved", "Stable", "Needs Focus"

class ShareResponse(BaseModel):
    share_url: str
    message: str

class TransformationComparisonResponse(BaseModel):
    baseline_image_url: Optional[str] = None
    current_image_url: Optional[str] = None
    transformation_score: int # 0-100
    qualitative_feedback: str
    metrics: List[ComparisonMetric]
    generated_at: datetime

class GrowthDomain(BaseModel):
    id: str
    title: str # e.g. "Mastery Challenge"
    description: str
    icon: str # key for frontend icon
    is_locked: bool
    unlock_criteria: str

class NextStepRecommendation(BaseModel):
    primary_recommendation: GrowthDomain
    alternatives: List[GrowthDomain]
    user_context: str # e.g. "Based on your 22-day streak..."


# --- Phase 5: Community Schemas ---

class LeaderboardEntry(BaseModel):
    rank: int
    user_name: str
    streak: int
    avatar_url: Optional[str] = None
    is_current_user: bool = False

# --- Phase 5C: Monetization Schemas ---

class PurchaseRequest(BaseModel):
    level_id: int
    item_type: str = "level" # "level" or "streak_freeze"
    use_coins: bool = False
    is_bundle: bool = False

class PurchaseResponse(BaseModel):
    success: bool
    transaction_id: str
    final_price: int
    coins_deducted: int
    message: str
    new_coin_balance: int
