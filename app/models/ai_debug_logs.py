"""
AI Debug Logs Model
Stores step-by-step logs of AI operations for transparency and debugging
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from app.db.session import Base


class AIDebugLog(Base):
    """Stores individual steps in AI processing for transparency"""
    __tablename__ = "ai_debug_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), nullable=False, index=True)  # Groups related steps
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
    # Step info
    step_number = Column(Integer, nullable=False)  # Order of execution (1, 2, 3...)
    step_name = Column(String(100), nullable=False)  # e.g., "topic_extraction", "validation"
    step_description = Column(String(500))  # Human readable description
    
    # Input/Output
    input_summary = Column(Text)  # Truncated input for display
    input_full = Column(Text)  # Full input (may be large)
    output_summary = Column(Text)  # Truncated output for display
    output_full = Column(Text)  # Full output JSON
    
    # AI Model info
    model_used = Column(String(50))  # e.g., "grok-4.1", "llama-3.1-8b"
    provider = Column(String(50))  # e.g., "grok", "openrouter"
    tokens_used = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    
    # Performance
    duration_ms = Column(Integer)  # How long the step took
    
    # Status
    success = Column(Boolean, default=True)
    is_fallback = Column(Boolean, default=False)  # If fallback logic was used
    error_message = Column(Text)
    
    # Context
    context_type = Column(String(50))  # e.g., "drill_report", "topic_validation"
    related_entity_id = Column(String(100))  # e.g., question_id, video_id


class AIDebugSession(Base):
    """Groups related debug logs into a session"""
    __tablename__ = "ai_debug_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Session info
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    completed_at = Column(DateTime(timezone=True))
    
    # Type of operation
    operation_type = Column(String(50))  # e.g., "drill_evaluation", "topic_check"
    operation_status = Column(String(50), default="in_progress")  # in_progress, completed, failed
    
    # Summary
    total_steps = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_duration_ms = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Result
    final_result_summary = Column(Text)  # Brief summary of the final outcome
    had_errors = Column(Boolean, default=False)
    had_fallbacks = Column(Boolean, default=False)
