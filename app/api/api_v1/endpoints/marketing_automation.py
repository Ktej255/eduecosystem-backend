"""Marketing Automation API endpoints."""
from typing import Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app import models
from app.api import deps
from app.models.marketing_automation import (
    CommunicationTemplate,
    MarketingWorkflow,
    WorkflowStep,
    WorkflowExecution,
    MessageLog,
    AutomationAnalytics,
)
from app.models.lead import Lead
from app.schemas.marketing_automation import (
    Template, TemplateCreate, TemplateUpdate,
    Workflow, WorkflowCreate, WorkflowUpdate, WorkflowSummary,
    WorkflowStep as WorkflowStepSchema, WorkflowStepCreate,
    Execution, ExecutionCreate,
    MessageLog as MessageLogSchema,
    AutomationDashboard, ChannelAnalytics, WorkflowAnalytics,
    TriggerWorkflowRequest, SendMessageRequest,
)

router = APIRouter()


# ============================================================================
# TEMPLATES
# ============================================================================

@router.get("/templates", response_model=List[Template])
def get_templates(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    channel: Optional[str] = None,
    category: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get communication templates."""
    query = db.query(CommunicationTemplate).filter(CommunicationTemplate.is_active == True)
    
    if channel:
        query = query.filter(CommunicationTemplate.channel == channel)
    if category:
        query = query.filter(CommunicationTemplate.category == category)
    
    return query.offset(skip).limit(limit).all()


@router.post("/templates", response_model=Template)
def create_template(
    template_in: TemplateCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new communication template."""
    template = CommunicationTemplate(
        **template_in.dict(),
        created_by=current_user.id
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/templates/{template_id}", response_model=Template)
def get_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get a specific template."""
    template = db.query(CommunicationTemplate).filter(CommunicationTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/templates/{template_id}", response_model=Template)
def update_template(
    template_id: int,
    template_in: TemplateUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a template."""
    template = db.query(CommunicationTemplate).filter(CommunicationTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = template_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Soft delete a template."""
    template = db.query(CommunicationTemplate).filter(CommunicationTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.is_active = False
    db.commit()
    return {"message": "Template deleted"}


# ============================================================================
# WORKFLOWS
# ============================================================================

@router.get("/workflows", response_model=List[WorkflowSummary])
def get_workflows(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all marketing workflows."""
    query = db.query(MarketingWorkflow)
    
    if status:
        query = query.filter(MarketingWorkflow.status == status)
    
    workflows = query.order_by(MarketingWorkflow.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for w in workflows:
        steps_count = db.query(WorkflowStep).filter(WorkflowStep.workflow_id == w.id).count()
        result.append({
            "id": w.id,
            "name": w.name,
            "status": w.status,
            "trigger_type": w.trigger_type,
            "total_enrolled": w.total_enrolled,
            "total_completed": w.total_completed,
            "total_converted": w.total_converted,
            "steps_count": steps_count,
            "created_at": w.created_at,
        })
    
    return result


@router.post("/workflows", response_model=Workflow)
def create_workflow(
    workflow_in: WorkflowCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new marketing workflow."""
    # Create workflow
    workflow_data = workflow_in.dict(exclude={"steps"})
    workflow = MarketingWorkflow(**workflow_data, created_by=current_user.id)
    db.add(workflow)
    db.flush()
    
    # Create steps if provided
    if workflow_in.steps:
        for step_data in workflow_in.steps:
            step = WorkflowStep(**step_data.dict(), workflow_id=workflow.id)
            db.add(step)
    
    db.commit()
    db.refresh(workflow)
    return workflow


@router.get("/workflows/{workflow_id}", response_model=Workflow)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get a specific workflow with its steps."""
    workflow = db.query(MarketingWorkflow).filter(MarketingWorkflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/workflows/{workflow_id}", response_model=Workflow)
def update_workflow(
    workflow_id: int,
    workflow_in: WorkflowUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a workflow."""
    workflow = db.query(MarketingWorkflow).filter(MarketingWorkflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    update_data = workflow_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)
    
    db.commit()
    db.refresh(workflow)
    return workflow


@router.post("/workflows/{workflow_id}/activate")
def activate_workflow(
    workflow_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Activate a workflow."""
    workflow = db.query(MarketingWorkflow).filter(MarketingWorkflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Validate workflow has steps
    steps_count = db.query(WorkflowStep).filter(WorkflowStep.workflow_id == workflow_id).count()
    if steps_count == 0:
        raise HTTPException(status_code=400, detail="Workflow must have at least one step")
    
    workflow.status = "ACTIVE"
    db.commit()
    return {"message": "Workflow activated", "status": "ACTIVE"}


@router.post("/workflows/{workflow_id}/pause")
def pause_workflow(
    workflow_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Pause a workflow."""
    workflow = db.query(MarketingWorkflow).filter(MarketingWorkflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow.status = "PAUSED"
    db.commit()
    return {"message": "Workflow paused", "status": "PAUSED"}


# ============================================================================
# WORKFLOW STEPS
# ============================================================================

@router.post("/workflows/{workflow_id}/steps", response_model=WorkflowStepSchema)
def add_workflow_step(
    workflow_id: int,
    step_in: WorkflowStepCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Add a step to a workflow."""
    workflow = db.query(MarketingWorkflow).filter(MarketingWorkflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    step = WorkflowStep(**step_in.dict(), workflow_id=workflow_id)
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


@router.put("/workflows/{workflow_id}/steps/{step_id}", response_model=WorkflowStepSchema)
def update_workflow_step(
    workflow_id: int,
    step_id: int,
    step_in: WorkflowStepCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a workflow step."""
    step = db.query(WorkflowStep).filter(
        and_(WorkflowStep.id == step_id, WorkflowStep.workflow_id == workflow_id)
    ).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    update_data = step_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(step, field, value)
    
    db.commit()
    db.refresh(step)
    return step


@router.delete("/workflows/{workflow_id}/steps/{step_id}")
def delete_workflow_step(
    workflow_id: int,
    step_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Delete a workflow step."""
    step = db.query(WorkflowStep).filter(
        and_(WorkflowStep.id == step_id, WorkflowStep.workflow_id == workflow_id)
    ).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    db.delete(step)
    db.commit()
    return {"message": "Step deleted"}


# ============================================================================
# TRIGGER & EXECUTION
# ============================================================================

@router.post("/trigger")
def trigger_workflow(
    request: TriggerWorkflowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Manually trigger a workflow for specific leads."""
    if request.workflow_id:
        workflow = db.query(MarketingWorkflow).filter(
            and_(MarketingWorkflow.id == request.workflow_id, MarketingWorkflow.status == "ACTIVE")
        ).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Active workflow not found")
        workflows = [workflow]
    else:
        workflows = db.query(MarketingWorkflow).filter(
            MarketingWorkflow.status == "ACTIVE"
        ).all()
    
    executions_created = 0
    for lead_id in request.lead_ids:
        # Verify lead exists
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            continue
        
        for workflow in workflows:
            # Check if lead already in workflow (unless re-entry allowed)
            if not workflow.allow_re_entry:
                existing = db.query(WorkflowExecution).filter(
                    and_(
                        WorkflowExecution.workflow_id == workflow.id,
                        WorkflowExecution.lead_id == lead_id,
                        WorkflowExecution.status.in_(["PENDING", "RUNNING"])
                    )
                ).first()
                if existing:
                    continue
            
            # Get first step
            first_step = db.query(WorkflowStep).filter(
                WorkflowStep.workflow_id == workflow.id
            ).order_by(WorkflowStep.order_index).first()
            
            if not first_step:
                continue
            
            # Create execution
            execution = WorkflowExecution(
                workflow_id=workflow.id,
                lead_id=lead_id,
                status="RUNNING",
                current_step_id=first_step.id,
                started_at=datetime.utcnow(),
                execution_log=[{
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "WORKFLOW_STARTED",
                    "step_id": first_step.id
                }]
            )
            db.add(execution)
            
            # Update workflow stats
            workflow.total_enrolled += 1
            
            executions_created += 1
    
    db.commit()
    
    return {
        "message": f"Triggered {executions_created} workflow executions",
        "executions_created": executions_created
    }


@router.get("/executions", response_model=List[Execution])
def get_executions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    workflow_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get workflow executions."""
    query = db.query(WorkflowExecution)
    
    if workflow_id:
        query = query.filter(WorkflowExecution.workflow_id == workflow_id)
    if status:
        query = query.filter(WorkflowExecution.status == status)
    
    return query.order_by(WorkflowExecution.started_at.desc()).offset(skip).limit(limit).all()


# ============================================================================
# SEND MESSAGE
# ============================================================================

@router.post("/send-message")
def send_message(
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Send a message to leads using a template."""
    template = db.query(CommunicationTemplate).filter(
        CommunicationTemplate.id == request.template_id
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    messages_queued = 0
    for lead_id in request.lead_ids:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            continue
        
        # Determine recipient based on channel
        recipient = None
        if request.channel == "EMAIL" and lead.email:
            recipient = lead.email
        elif request.channel in ["SMS", "WHATSAPP"] and lead.phone:
            recipient = lead.phone
        elif request.channel == "PUSH":
            recipient = f"user_{lead_id}"  # Push token would be stored separately
        
        if not recipient:
            continue
        
        # Replace tokens in body
        body = template.body
        body = body.replace("{{name}}", lead.name or "")
        body = body.replace("{{email}}", lead.email or "")
        body = body.replace("{{phone}}", lead.phone or "")
        
        # Create message log
        message = MessageLog(
            lead_id=lead_id,
            template_id=template.id,
            channel=request.channel.value,
            recipient=recipient,
            subject=template.subject,
            body=body,
            status="PENDING",
        )
        db.add(message)
        messages_queued += 1
    
    db.commit()
    
    # In production, you would queue these for actual sending via background task
    # background_tasks.add_task(process_message_queue)
    
    return {
        "message": f"Queued {messages_queued} messages for sending",
        "messages_queued": messages_queued
    }


# ============================================================================
# ANALYTICS DASHBOARD
# ============================================================================

@router.get("/dashboard", response_model=AutomationDashboard)
def get_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get marketing automation dashboard."""
    # Workflow stats
    total_workflows = db.query(MarketingWorkflow).count()
    active_workflows = db.query(MarketingWorkflow).filter(MarketingWorkflow.status == "ACTIVE").count()
    total_templates = db.query(CommunicationTemplate).filter(CommunicationTemplate.is_active == True).count()
    
    leads_in_workflows = db.query(WorkflowExecution).filter(
        WorkflowExecution.status.in_(["PENDING", "RUNNING"])
    ).count()
    
    # Message analytics (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    def get_channel_analytics(channel: str) -> dict:
        sent = db.query(MessageLog).filter(
            and_(MessageLog.channel == channel, MessageLog.created_at >= thirty_days_ago)
        ).count()
        delivered = db.query(MessageLog).filter(
            and_(MessageLog.channel == channel, MessageLog.delivered_at.isnot(None), MessageLog.created_at >= thirty_days_ago)
        ).count()
        opened = db.query(MessageLog).filter(
            and_(MessageLog.channel == channel, MessageLog.opened_at.isnot(None), MessageLog.created_at >= thirty_days_ago)
        ).count()
        clicked = db.query(MessageLog).filter(
            and_(MessageLog.channel == channel, MessageLog.clicked_at.isnot(None), MessageLog.created_at >= thirty_days_ago)
        ).count()
        
        return {
            "sent": sent,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "delivery_rate": (delivered / sent * 100) if sent > 0 else 0,
            "open_rate": (opened / delivered * 100) if delivered > 0 else 0,
            "click_rate": (clicked / opened * 100) if opened > 0 else 0,
        }
    
    # Recent executions
    recent_executions = db.query(WorkflowExecution).order_by(
        WorkflowExecution.started_at.desc()
    ).limit(10).all()
    
    # Top workflows
    top_workflows_query = db.query(MarketingWorkflow).order_by(
        MarketingWorkflow.total_enrolled.desc()
    ).limit(5).all()
    
    top_workflows = []
    for w in top_workflows_query:
        steps_count = db.query(WorkflowStep).filter(WorkflowStep.workflow_id == w.id).count()
        top_workflows.append({
            "id": w.id,
            "name": w.name,
            "status": w.status,
            "trigger_type": w.trigger_type,
            "total_enrolled": w.total_enrolled,
            "total_completed": w.total_completed,
            "total_converted": w.total_converted,
            "steps_count": steps_count,
            "created_at": w.created_at,
        })
    
    return {
        "total_workflows": total_workflows,
        "active_workflows": active_workflows,
        "total_templates": total_templates,
        "leads_in_workflows": leads_in_workflows,
        "email_analytics": get_channel_analytics("EMAIL"),
        "sms_analytics": get_channel_analytics("SMS"),
        "whatsapp_analytics": get_channel_analytics("WHATSAPP"),
        "push_analytics": get_channel_analytics("PUSH"),
        "recent_executions": recent_executions,
        "top_workflows": top_workflows,
    }


@router.get("/message-logs", response_model=List[MessageLogSchema])
def get_message_logs(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    channel: Optional[str] = None,
    status: Optional[str] = None,
    lead_id: Optional[int] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """Get message logs."""
    query = db.query(MessageLog)
    
    if channel:
        query = query.filter(MessageLog.channel == channel)
    if status:
        query = query.filter(MessageLog.status == status)
    if lead_id:
        query = query.filter(MessageLog.lead_id == lead_id)
    
    return query.order_by(MessageLog.created_at.desc()).offset(skip).limit(limit).all()
