"""Schemas for Marketing Automation."""
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ChannelType(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    PUSH = "PUSH"


class TriggerType(str, Enum):
    LEAD_CREATED = "LEAD_CREATED"
    LEAD_UPDATED = "LEAD_UPDATED"
    STAGE_CHANGED = "STAGE_CHANGED"
    FIELD_UPDATE = "FIELD_UPDATE"
    TIME_DELAY = "TIME_DELAY"
    SPECIFIC_DATE = "SPECIFIC_DATE"
    USER_ACTIVITY = "USER_ACTIVITY"
    MANUAL = "MANUAL"


class StepType(str, Enum):
    SEND_MESSAGE = "SEND_MESSAGE"
    WAIT = "WAIT"
    CONDITION = "CONDITION"
    UPDATE_FIELD = "UPDATE_FIELD"
    ASSIGN = "ASSIGN"


# ============================================================================
# Communication Templates
# ============================================================================

class TemplateBase(BaseModel):
    name: str
    channel: ChannelType
    subject: Optional[str] = None
    body: str
    html_body: Optional[str] = None
    available_tokens: Optional[List[str]] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    channel: Optional[ChannelType] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    html_body: Optional[str] = None
    available_tokens: Optional[List[str]] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class Template(TemplateBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Workflow Steps
# ============================================================================

class WorkflowStepBase(BaseModel):
    order_index: int
    name: str
    step_type: StepType
    channel: Optional[ChannelType] = None
    template_id: Optional[int] = None
    wait_duration_minutes: Optional[int] = None
    wait_until_date: Optional[datetime] = None
    wait_for_event: Optional[str] = None
    condition_config: Optional[Dict[str, Any]] = None
    true_next_step: Optional[int] = None
    false_next_step: Optional[int] = None
    field_updates: Optional[Dict[str, Any]] = None
    assign_to_user_id: Optional[int] = None
    assign_to_team: Optional[str] = None
    is_active: bool = True


class WorkflowStepCreate(WorkflowStepBase):
    pass


class WorkflowStep(WorkflowStepBase):
    id: int
    workflow_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Marketing Workflows
# ============================================================================

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: TriggerType
    trigger_config: Optional[Dict[str, Any]] = None
    audience_filters: Optional[Dict[str, Any]] = None
    allow_re_entry: bool = False
    exit_on_conversion: bool = True


class WorkflowCreate(WorkflowBase):
    steps: Optional[List[WorkflowStepCreate]] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    trigger_type: Optional[TriggerType] = None
    trigger_config: Optional[Dict[str, Any]] = None
    audience_filters: Optional[Dict[str, Any]] = None
    allow_re_entry: Optional[bool] = None
    exit_on_conversion: Optional[bool] = None


class Workflow(WorkflowBase):
    id: int
    status: str
    total_enrolled: int
    total_completed: int
    total_converted: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    steps: List[WorkflowStep] = []

    class Config:
        from_attributes = True


class WorkflowSummary(BaseModel):
    id: int
    name: str
    status: str
    trigger_type: str
    total_enrolled: int
    total_completed: int
    total_converted: int
    steps_count: int
    created_at: datetime


# ============================================================================
# Workflow Execution
# ============================================================================

class ExecutionBase(BaseModel):
    workflow_id: int
    lead_id: int


class ExecutionCreate(ExecutionBase):
    pass


class Execution(ExecutionBase):
    id: int
    status: str
    current_step_id: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    next_action_at: Optional[datetime] = None
    execution_log: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    retry_count: int

    class Config:
        from_attributes = True


# ============================================================================
# Message Log
# ============================================================================

class MessageLogBase(BaseModel):
    channel: ChannelType
    recipient: str
    subject: Optional[str] = None
    body: Optional[str] = None


class MessageLog(MessageLogBase):
    id: int
    lead_id: Optional[int] = None
    workflow_execution_id: Optional[int] = None
    template_id: Optional[int] = None
    status: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Analytics
# ============================================================================

class ChannelAnalytics(BaseModel):
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0


class WorkflowAnalytics(BaseModel):
    total_enrolled: int = 0
    total_completed: int = 0
    total_converted: int = 0
    completion_rate: float = 0.0
    conversion_rate: float = 0.0


class AutomationDashboard(BaseModel):
    total_workflows: int
    active_workflows: int
    total_templates: int
    leads_in_workflows: int
    
    email_analytics: ChannelAnalytics
    sms_analytics: ChannelAnalytics
    whatsapp_analytics: ChannelAnalytics
    push_analytics: ChannelAnalytics
    
    recent_executions: List[Execution]
    top_workflows: List[WorkflowSummary]


# ============================================================================
# Trigger Request
# ============================================================================

class TriggerWorkflowRequest(BaseModel):
    lead_ids: List[int]
    workflow_id: Optional[int] = None  # If None, triggers all matching workflows


class SendMessageRequest(BaseModel):
    lead_ids: List[int]
    template_id: int
    channel: ChannelType
    scheduled_at: Optional[datetime] = None
