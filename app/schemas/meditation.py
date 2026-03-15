"""
Meditation Session System - Pydantic Schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class MeditationProcessBase(BaseModel):
    name: str
    description: Optional[str] = None
    order: int = 1
    duration_minutes: int = 5
    level: int = 1


class MeditationProcessCreate(MeditationProcessBase):
    pass


class MeditationProcessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    duration_minutes: Optional[int] = None
    video_url: Optional[str] = None
    is_active: Optional[bool] = None
    # Audio assets for immersive player
    announcement_audio_url: Optional[str] = None
    background_music_url: Optional[str] = None
    bell_sound_url: Optional[str] = None


class MeditationProcessResponse(MeditationProcessBase):
    id: int
    video_url: Optional[str] = None
    video_filename: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    # Audio assets for immersive player
    announcement_audio_url: Optional[str] = None
    background_music_url: Optional[str] = None
    bell_sound_url: Optional[str] = None

    class Config:
        from_attributes = True


class MeditationProgressResponse(BaseModel):
    id: int
    user_id: int
    current_level: int
    current_day: int
    total_streak: int
    preferred_session: str
    unlocked_levels: int
    last_practice_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class MeditationDayOverview(BaseModel):
    """Overview of processes for a specific day"""
    level: int
    day_number: int
    total_processes: int
    is_unlock_day: bool  # Whether new processes are introduced today
    new_process_start: Optional[int] = None  # First new process number (if unlock day)
    new_process_end: Optional[int] = None    # Last new process number (if unlock day)
    processes: List[MeditationProcessResponse]
    completed_processes: List[int]  # IDs of completed processes
    is_day_completed: bool


class MeditationLevelInfo(BaseModel):
    """Info about a meditation level"""
    level: int
    name: str
    description: str
    total_days: int
    completed_days: int
    is_unlocked: bool
    is_current: bool
    is_completed: bool


class MeditationOverviewResponse(BaseModel):
    """Overall meditation progress overview"""
    current_level: int
    current_day: int
    total_streak: int
    last_practice_date: Optional[datetime] = None
    preferred_session: str
    levels: List[MeditationLevelInfo]
    total_days_completed: int
    total_days_remaining: int
    # Today's session info
    todays_processes: int
    is_unlock_day: bool


class MeditationDayInfo(BaseModel):
    """Info about a specific day in the calendar"""
    day_number: int
    is_unlocked: bool
    is_completed: bool
    completed_at: Optional[str] = None
    unlock_date: Optional[str] = None
    processes_count: int


class MeditationLevelDetailResponse(BaseModel):
    """Detailed view of a level with all days"""
    level: int
    name: str
    description: str
    total_days: int
    days: List[MeditationDayInfo]


class ProcessCompleteRequest(BaseModel):
    watched_video: bool = False


class ProcessCompleteResponse(BaseModel):
    success: bool
    message: str
    process_id: int
    all_processes_done: bool


class DayCompleteRequest(BaseModel):
    session_type: str = "morning"  # morning/night
    notes: Optional[str] = None


class DayCompleteResponse(BaseModel):
    success: bool
    message: str
    new_streak: int
    level_completed: bool = False
    next_level_unlocked: bool = False


# ============================================================================
# Experience Recording Schemas (AI Progress Tracking)
# ============================================================================

class PreSessionExperienceCreate(BaseModel):
    """Schema for recording pre-session mental state"""
    level: int
    day_number: int
    stress_level: int  # 1-10
    anxiety_level: int  # 1-10
    focus_level: int  # 1-10
    emotional_state: str  # Calm/Anxious/Stressed/Overwhelmed/Neutral
    concerns: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "level": 1,
                "day_number": 5,
                "stress_level": 7,
                "anxiety_level": 6,
                "focus_level": 4,
                "emotional_state": "Stressed",
                "concerns": "Feeling overwhelmed with upcoming exams"
            }
        }


class PostSessionExperienceCreate(BaseModel):
    """Schema for recording post-session experience"""
    experience_id: int
    stress_level: int  # 1-10
    anxiety_level: int  # 1-10
    focus_level: int  # 1-10
    emotional_state: str  # Calm/Anxious/Stressed/Overwhelmed/Neutral
    insights: Optional[str] = None
    effectiveness_rating: int  # 1-5 stars
    
    class Config:
        json_schema_extra = {
            "example": {
                "experience_id": 123,
                "stress_level": 3,
                "anxiety_level": 2,
                "focus_level": 8,
                "emotional_state": "Calm",
                "insights": "Feeling much more centered and focused after the session",
                "effectiveness_rating": 5
            }
        }


class ExperienceResponse(BaseModel):
    """Response schema for experience data"""
    id: int
    user_id: int
    day_completion_id: int
    
    # Pre-session
    pre_stress_level: int
    pre_anxiety_level: int
    pre_focus_level: int
    pre_emotional_state: str
    pre_concerns: Optional[str] = None
    pre_recorded_at: datetime
    
    # Post-session
    post_stress_level: Optional[int] = None
    post_anxiety_level: Optional[int] = None
    post_focus_level: Optional[int] = None
    post_emotional_state: Optional[str] = None
    post_insights: Optional[str] = None
    post_effectiveness_rating: Optional[int] = None
    post_recorded_at: Optional[datetime] = None
    
    # Improvements
    stress_improvement: Optional[int] = None
    anxiety_improvement: Optional[int] = None
    focus_improvement: Optional[int] = None
    overall_improvement_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    """Overall analytics from all experiences"""
    total_sessions: int
    average_stress_improvement: float
    average_anxiety_improvement: float
    average_focus_improvement: float
    overall_wellbeing_score: float  # 0-100
    trend_direction: str  # "improving", "stable", "declining"
    best_time_of_day: Optional[str] = None  # "morning" or "night"
    most_effective_processes: List[int] = []  # Process IDs


class GraphDataPoint(BaseModel):
    """Single data point for graphs"""
    date: str  # ISO format date
    stress_level: Optional[int] = None
    anxiety_level: Optional[int] = None
    focus_level: Optional[int] = None
    improvement_score: Optional[float] = None


class GraphDataResponse(BaseModel):
    """Graph data for visualization"""
    pre_session_data: List[GraphDataPoint]
    post_session_data: List[GraphDataPoint]
    improvement_data: List[GraphDataPoint]
    date_range: str  # e.g., "Last 30 days"


# ============================================================================
# PAYMENT SCHEMAS (Phase 2)
# ============================================================================

class LevelPricingResponse(BaseModel):
    """Pricing information for a meditation level"""
    level: int
    name: str
    description: str
    price: float
    currency: str
    free_processes: Optional[int] = None


class BundlePricingResponse(BaseModel):
    """Bundle pricing information"""
    name: str
    description: str
    levels: List[int]
    price: float
    currency: str
    savings: float


class PricingResponse(BaseModel):
    """Complete pricing information"""
    levels: List[LevelPricingResponse]
    bundles: List[BundlePricingResponse]


class PurchaseInitiateRequest(BaseModel):
    """Request to initiate a level purchase"""
    level: int


class PurchaseInitiateResponse(BaseModel):
    """Response with Cashfree order details"""
    order_id: str
    payment_session_id: str
    amount: float
    currency: str
    level: int
    customer_id: str


class PaymentVerificationRequest(BaseModel):
    """Request to verify Cashfree payment"""
    order_id: str


class PurchaseResponse(BaseModel):
    """Purchase record response"""
    id: int
    user_id: int
    level: int
    amount_paid: float
    currency: str
    payment_status: str
    purchased_at: Optional[datetime] = None
    payment_method: Optional[str] = None
    receipt_url: Optional[str] = None

    class Config:
        from_attributes = True


class PurchaseHistoryResponse(BaseModel):
    """User's purchase history"""
    purchases: List[PurchaseResponse]
    total_spent: float
    levels_owned: List[int]

