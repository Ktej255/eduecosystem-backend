"""
AI Debug Service
Logs and tracks every AI operation step-by-step for transparency
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
from sqlalchemy.orm import Session

from app.models.ai_debug_logs import AIDebugLog, AIDebugSession


class AIDebugService:
    """Service for logging and retrieving AI operation steps"""

    def __init__(self):
        self._current_sessions: Dict[str, dict] = {}  # In-memory tracking

    def start_session(
        self,
        db: Session,
        operation_type: str,
        student_id: Optional[int] = None,
        related_entity_id: Optional[str] = None
    ) -> str:
        """
        Start a new debug session.
        
        Args:
            db: Database session
            operation_type: Type of operation (e.g., "drill_evaluation")
            student_id: Optional student ID
            related_entity_id: Optional related entity (question_id, etc.)
            
        Returns:
            session_id for logging subsequent steps
        """
        session_id = str(uuid.uuid4())[:16]
        
        # Create session record
        session = AIDebugSession(
            session_id=session_id,
            student_id=student_id,
            operation_type=operation_type,
            operation_status="in_progress"
        )
        db.add(session)
        db.commit()
        
        # Track in memory
        self._current_sessions[session_id] = {
            "step_count": 0,
            "total_tokens": 0,
            "total_duration": 0,
            "total_cost": 0.0,
            "start_time": datetime.utcnow(),
            "related_entity_id": related_entity_id
        }
        
        return session_id

    async def log_step(
        self,
        db: Session,
        session_id: str,
        step_name: str,
        step_description: str,
        input_data: Any,
        output_data: Any,
        model_used: str = "unknown",
        provider: str = "unknown",
        tokens_used: int = 0,
        duration_ms: int = 0,
        success: bool = True,
        is_fallback: bool = False,
        error_message: Optional[str] = None,
        context_type: str = "general"
    ) -> None:
        """
        Log a single AI processing step.
        
        Args:
            db: Database session
            session_id: The session this step belongs to
            step_name: Name of the step (e.g., "topic_extraction")
            step_description: Human readable description
            input_data: Input data (will be JSON serialized)
            output_data: Output data (will be JSON serialized)
            model_used: AI model used
            provider: Provider (grok, openrouter, etc.)
            tokens_used: Number of tokens consumed
            duration_ms: How long the step took
            success: Whether the step succeeded
            is_fallback: Whether fallback logic was used
            error_message: Error message if failed
            context_type: Context category
        """
        # Get session tracking
        session_info = self._current_sessions.get(session_id, {
            "step_count": 0,
            "total_tokens": 0,
            "total_duration": 0,
            "total_cost": 0.0
        })
        
        session_info["step_count"] += 1
        session_info["total_tokens"] += tokens_used
        session_info["total_duration"] += duration_ms
        
        # Estimate cost (rough estimate based on model)
        cost = self._estimate_cost(model_used, tokens_used)
        session_info["total_cost"] += cost
        
        # Serialize input/output
        input_str = self._safe_serialize(input_data)
        output_str = self._safe_serialize(output_data)
        
        # Create log entry
        log = AIDebugLog(
            session_id=session_id,
            step_number=session_info["step_count"],
            step_name=step_name,
            step_description=step_description,
            input_summary=input_str[:500] if input_str else None,
            input_full=input_str,
            output_summary=output_str[:500] if output_str else None,
            output_full=output_str,
            model_used=model_used,
            provider=provider,
            tokens_used=tokens_used,
            estimated_cost=cost,
            duration_ms=duration_ms,
            success=success,
            is_fallback=is_fallback,
            error_message=error_message,
            context_type=context_type,
            related_entity_id=session_info.get("related_entity_id")
        )
        db.add(log)
        db.commit()
        
        # Update session tracking
        self._current_sessions[session_id] = session_info

    def end_session(
        self,
        db: Session,
        session_id: str,
        final_result: Any,
        had_errors: bool = False,
        had_fallbacks: bool = False
    ) -> None:
        """
        End a debug session and update summary.
        
        Args:
            db: Database session
            session_id: The session to end
            final_result: Summary of final result
            had_errors: Whether any errors occurred
            had_fallbacks: Whether any fallbacks were used
        """
        session_info = self._current_sessions.get(session_id, {})
        
        # Update session record
        session = db.query(AIDebugSession).filter(
            AIDebugSession.session_id == session_id
        ).first()
        
        if session:
            session.completed_at = datetime.utcnow()
            session.operation_status = "completed" if not had_errors else "failed"
            session.total_steps = session_info.get("step_count", 0)
            session.total_tokens = session_info.get("total_tokens", 0)
            session.total_duration_ms = session_info.get("total_duration", 0)
            session.total_cost = session_info.get("total_cost", 0.0)
            session.final_result_summary = self._safe_serialize(final_result)[:1000]
            session.had_errors = had_errors
            session.had_fallbacks = had_fallbacks
            db.commit()
        
        # Cleanup memory
        if session_id in self._current_sessions:
            del self._current_sessions[session_id]

    def get_session_logs(
        self,
        db: Session,
        session_id: str
    ) -> List[Dict]:
        """Get all logs for a session"""
        logs = db.query(AIDebugLog).filter(
            AIDebugLog.session_id == session_id
        ).order_by(AIDebugLog.step_number).all()
        
        return [
            {
                "step_number": log.step_number,
                "step_name": log.step_name,
                "step_description": log.step_description,
                "input_summary": log.input_summary,
                "output_summary": log.output_summary,
                "model_used": log.model_used,
                "provider": log.provider,
                "tokens_used": log.tokens_used,
                "duration_ms": log.duration_ms,
                "success": log.success,
                "is_fallback": log.is_fallback,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]

    def get_recent_sessions(
        self,
        db: Session,
        limit: int = 50,
        operation_type: Optional[str] = None
    ) -> List[Dict]:
        """Get recent debug sessions"""
        query = db.query(AIDebugSession).order_by(
            AIDebugSession.created_at.desc()
        )
        
        if operation_type:
            query = query.filter(AIDebugSession.operation_type == operation_type)
        
        sessions = query.limit(limit).all()
        
        return [
            {
                "session_id": s.session_id,
                "student_id": s.student_id,
                "operation_type": s.operation_type,
                "operation_status": s.operation_status,
                "total_steps": s.total_steps,
                "total_tokens": s.total_tokens,
                "total_duration_ms": s.total_duration_ms,
                "total_cost": s.total_cost,
                "had_errors": s.had_errors,
                "had_fallbacks": s.had_fallbacks,
                "final_result_summary": s.final_result_summary,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None
            }
            for s in sessions
        ]

    def get_step_details(
        self,
        db: Session,
        session_id: str,
        step_number: int
    ) -> Optional[Dict]:
        """Get full details for a specific step"""
        log = db.query(AIDebugLog).filter(
            AIDebugLog.session_id == session_id,
            AIDebugLog.step_number == step_number
        ).first()
        
        if not log:
            return None
        
        return {
            "step_number": log.step_number,
            "step_name": log.step_name,
            "step_description": log.step_description,
            "input_full": log.input_full,
            "output_full": log.output_full,
            "model_used": log.model_used,
            "provider": log.provider,
            "tokens_used": log.tokens_used,
            "estimated_cost": log.estimated_cost,
            "duration_ms": log.duration_ms,
            "success": log.success,
            "is_fallback": log.is_fallback,
            "error_message": log.error_message,
            "context_type": log.context_type,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }

    def _safe_serialize(self, data: Any) -> str:
        """Safely serialize data to JSON string"""
        if data is None:
            return ""
        if isinstance(data, str):
            return data
        try:
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            return str(data)

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost based on model and tokens"""
        # Rough cost estimates per 1K tokens
        costs = {
            "grok": 0.002,
            "llama-3.1-8b": 0.0001,
            "llama-3.2-90b": 0.001,
            "gemini": 0.0005,
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002
        }
        
        for model_key, cost in costs.items():
            if model_key.lower() in model.lower():
                return (tokens / 1000) * cost
        
        return (tokens / 1000) * 0.001  # Default estimate


# Global instance
ai_debug_service = AIDebugService()
