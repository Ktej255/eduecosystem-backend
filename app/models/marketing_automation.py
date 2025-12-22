"""Marketing Automation Models."""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class ChannelType(str, enum.Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    PUSH = "PUSH"


class TriggerType(str, enum.Enum):
    LEAD_CREATED = "LEAD_CREATED"
    LEAD_UPDATED = "LEAD_UPDATED"
    STAGE_CHANGED = "STAGE_CHANGED"
    FIELD_UPDATE = "FIELD_UPDATE"
    TIME_DELAY = "TIME_DELAY"
    SPECIFIC_DATE = "SPECIFIC_DATE"
    USER_ACTIVITY = "USER_ACTIVITY"
    MANUAL = "MANUAL"


class WorkflowStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class ExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CommunicationTemplate(Base):
    """Templates for email, SMS, WhatsApp, and push notifications."""
    __tablename__ = "communication_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    channel = Column(String, nullable=False, index=True)  # EMAIL, SMS, WHATSAPP, PUSH
    
    # Content
    subject = Column(String, nullable=True)  # For emails
    body = Column(Text, nullable=False)
    html_body = Column(Text, nullable=True)  # For HTML emails
    
    # Personalization tokens (JSON list of available tokens)
    available_tokens = Column(JSON, nullable=True)  # ["{{name}}", "{{course}}", "{{stage}}"]
    
    # Media attachments (for WhatsApp)
    media_url = Column(String, nullable=True)
    media_type = Column(String, nullable=True)  # image, video, document
    
    # Metadata
    category = Column(String, nullable=True, index=True)  # welcome, reminder, followup, etc.
    is_active = Column(Boolean, default=True)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    workflow_steps = relationship("WorkflowStep", back_populates="template")


class MarketingWorkflow(Base):
    """Automated marketing workflow definition."""
    __tablename__ = "marketing_workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    status = Column(String, default="DRAFT", index=True)  # DRAFT, ACTIVE, PAUSED, ARCHIVED
    
    # Trigger configuration
    trigger_type = Column(String, nullable=False)  # LEAD_CREATED, STAGE_CHANGED, etc.
    trigger_config = Column(JSON, nullable=True)  # Additional trigger conditions
    
    # Target audience filters
    audience_filters = Column(JSON, nullable=True)  # {"stage": "NEW", "source": "WEBSITE"}
    
    # Workflow settings
    allow_re_entry = Column(Boolean, default=False)  # Can a lead enter workflow multiple times
    exit_on_conversion = Column(Boolean, default=True)  # Exit if lead converts
    
    # Analytics
    total_enrolled = Column(Integer, default=0)
    total_completed = Column(Integer, default=0)
    total_converted = Column(Integer, default=0)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    steps = relationship("WorkflowStep", back_populates="workflow", order_by="WorkflowStep.order_index")
    executions = relationship("WorkflowExecution", back_populates="workflow")


class WorkflowStep(Base):
    """Individual step in a marketing workflow."""
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("marketing_workflows.id"), nullable=False, index=True)
    
    order_index = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    step_type = Column(String, nullable=False)  # SEND_MESSAGE, WAIT, CONDITION, UPDATE_FIELD, ASSIGN
    
    # For SEND_MESSAGE steps
    channel = Column(String, nullable=True)  # EMAIL, SMS, WHATSAPP, PUSH
    template_id = Column(Integer, ForeignKey("communication_templates.id"), nullable=True)
    
    # For WAIT steps
    wait_duration_minutes = Column(Integer, nullable=True)
    wait_until_date = Column(DateTime, nullable=True)
    wait_for_event = Column(String, nullable=True)  # e.g., "EMAIL_OPENED"
    
    # For CONDITION steps (branching)
    condition_config = Column(JSON, nullable=True)  # {"field": "stage", "operator": "equals", "value": "INTERESTED"}
    true_next_step = Column(Integer, nullable=True)
    false_next_step = Column(Integer, nullable=True)
    
    # For UPDATE_FIELD steps
    field_updates = Column(JSON, nullable=True)  # {"stage": "CONTACTED", "assigned_to": 5}
    
    # For ASSIGN steps
    assign_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assign_to_team = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    workflow = relationship("MarketingWorkflow", back_populates="steps")
    template = relationship("CommunicationTemplate", back_populates="workflow_steps")


class WorkflowExecution(Base):
    """Track individual workflow executions for leads."""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("marketing_workflows.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    status = Column(String, default="PENDING", index=True)  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    current_step_id = Column(Integer, ForeignKey("workflow_steps.id"), nullable=True)
    
    # Progress tracking
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    next_action_at = Column(DateTime(timezone=True), nullable=True)  # When to execute next step
    
    # Execution log
    execution_log = Column(JSON, nullable=True)  # List of {step_id, status, timestamp, details}
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    workflow = relationship("MarketingWorkflow", back_populates="executions")


class MessageLog(Base):
    """Log of all sent messages across channels."""
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("communication_templates.id"), nullable=True)
    
    channel = Column(String, nullable=False, index=True)  # EMAIL, SMS, WHATSAPP, PUSH
    recipient = Column(String, nullable=False)  # Email or phone number
    
    # Content (after token replacement)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    
    # Status
    status = Column(String, default="PENDING", index=True)  # PENDING, SENT, DELIVERED, FAILED, BOUNCED
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Engagement tracking
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    
    # Provider response
    provider_message_id = Column(String, nullable=True)
    provider_response = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AutomationAnalytics(Base):
    """Daily analytics for marketing automation."""
    __tablename__ = "automation_analytics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    workflow_id = Column(Integer, ForeignKey("marketing_workflows.id"), nullable=True, index=True)
    
    # Message metrics
    emails_sent = Column(Integer, default=0)
    emails_delivered = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    
    sms_sent = Column(Integer, default=0)
    sms_delivered = Column(Integer, default=0)
    
    whatsapp_sent = Column(Integer, default=0)
    whatsapp_delivered = Column(Integer, default=0)
    whatsapp_read = Column(Integer, default=0)
    
    push_sent = Column(Integer, default=0)
    push_clicked = Column(Integer, default=0)
    
    # Workflow metrics
    workflow_enrollments = Column(Integer, default=0)
    workflow_completions = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
