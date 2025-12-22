"""Add marketing automation tables

Revision ID: d2345678901b
Revises: c1234567890a
Create Date: 2025-12-17 08:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2345678901b'
down_revision: Union[str, Sequence[str], None] = 'c1234567890a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create marketing automation tables."""
    
    # Communication Templates
    op.create_table('communication_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('html_body', sa.Text(), nullable=True),
        sa.Column('available_tokens', sa.JSON(), nullable=True),
        sa.Column('media_url', sa.String(), nullable=True),
        sa.Column('media_type', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_templates_id'), 'communication_templates', ['id'], unique=False)
    op.create_index(op.f('ix_communication_templates_name'), 'communication_templates', ['name'], unique=False)
    op.create_index(op.f('ix_communication_templates_channel'), 'communication_templates', ['channel'], unique=False)
    op.create_index(op.f('ix_communication_templates_category'), 'communication_templates', ['category'], unique=False)

    # Marketing Workflows
    op.create_table('marketing_workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('trigger_type', sa.String(), nullable=False),
        sa.Column('trigger_config', sa.JSON(), nullable=True),
        sa.Column('audience_filters', sa.JSON(), nullable=True),
        sa.Column('allow_re_entry', sa.Boolean(), nullable=True),
        sa.Column('exit_on_conversion', sa.Boolean(), nullable=True),
        sa.Column('total_enrolled', sa.Integer(), nullable=True),
        sa.Column('total_completed', sa.Integer(), nullable=True),
        sa.Column('total_converted', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_marketing_workflows_id'), 'marketing_workflows', ['id'], unique=False)
    op.create_index(op.f('ix_marketing_workflows_name'), 'marketing_workflows', ['name'], unique=False)
    op.create_index(op.f('ix_marketing_workflows_status'), 'marketing_workflows', ['status'], unique=False)

    # Workflow Steps
    op.create_table('workflow_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('step_type', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('wait_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('wait_until_date', sa.DateTime(), nullable=True),
        sa.Column('wait_for_event', sa.String(), nullable=True),
        sa.Column('condition_config', sa.JSON(), nullable=True),
        sa.Column('true_next_step', sa.Integer(), nullable=True),
        sa.Column('false_next_step', sa.Integer(), nullable=True),
        sa.Column('field_updates', sa.JSON(), nullable=True),
        sa.Column('assign_to_user_id', sa.Integer(), nullable=True),
        sa.Column('assign_to_team', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['workflow_id'], ['marketing_workflows.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['communication_templates.id'], ),
        sa.ForeignKeyConstraint(['assign_to_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_steps_id'), 'workflow_steps', ['id'], unique=False)
    op.create_index(op.f('ix_workflow_steps_workflow_id'), 'workflow_steps', ['workflow_id'], unique=False)

    # Workflow Executions
    op.create_table('workflow_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('current_step_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_action_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_log', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workflow_id'], ['marketing_workflows.id'], ),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.ForeignKeyConstraint(['current_step_id'], ['workflow_steps.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_executions_id'), 'workflow_executions', ['id'], unique=False)
    op.create_index(op.f('ix_workflow_executions_workflow_id'), 'workflow_executions', ['workflow_id'], unique=False)
    op.create_index(op.f('ix_workflow_executions_lead_id'), 'workflow_executions', ['lead_id'], unique=False)
    op.create_index(op.f('ix_workflow_executions_status'), 'workflow_executions', ['status'], unique=False)

    # Message Logs
    op.create_table('message_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('workflow_execution_id', sa.Integer(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('recipient', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provider_message_id', sa.String(), nullable=True),
        sa.Column('provider_response', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.ForeignKeyConstraint(['workflow_execution_id'], ['workflow_executions.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['communication_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_logs_id'), 'message_logs', ['id'], unique=False)
    op.create_index(op.f('ix_message_logs_lead_id'), 'message_logs', ['lead_id'], unique=False)
    op.create_index(op.f('ix_message_logs_channel'), 'message_logs', ['channel'], unique=False)
    op.create_index(op.f('ix_message_logs_status'), 'message_logs', ['status'], unique=False)

    # Automation Analytics
    op.create_table('automation_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=True),
        sa.Column('emails_sent', sa.Integer(), nullable=True),
        sa.Column('emails_delivered', sa.Integer(), nullable=True),
        sa.Column('emails_opened', sa.Integer(), nullable=True),
        sa.Column('emails_clicked', sa.Integer(), nullable=True),
        sa.Column('sms_sent', sa.Integer(), nullable=True),
        sa.Column('sms_delivered', sa.Integer(), nullable=True),
        sa.Column('whatsapp_sent', sa.Integer(), nullable=True),
        sa.Column('whatsapp_delivered', sa.Integer(), nullable=True),
        sa.Column('whatsapp_read', sa.Integer(), nullable=True),
        sa.Column('push_sent', sa.Integer(), nullable=True),
        sa.Column('push_clicked', sa.Integer(), nullable=True),
        sa.Column('workflow_enrollments', sa.Integer(), nullable=True),
        sa.Column('workflow_completions', sa.Integer(), nullable=True),
        sa.Column('conversions', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['workflow_id'], ['marketing_workflows.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_analytics_id'), 'automation_analytics', ['id'], unique=False)
    op.create_index(op.f('ix_automation_analytics_date'), 'automation_analytics', ['date'], unique=False)
    op.create_index(op.f('ix_automation_analytics_workflow_id'), 'automation_analytics', ['workflow_id'], unique=False)


def downgrade() -> None:
    """Drop marketing automation tables."""
    op.drop_index(op.f('ix_automation_analytics_workflow_id'), table_name='automation_analytics')
    op.drop_index(op.f('ix_automation_analytics_date'), table_name='automation_analytics')
    op.drop_index(op.f('ix_automation_analytics_id'), table_name='automation_analytics')
    op.drop_table('automation_analytics')
    
    op.drop_index(op.f('ix_message_logs_status'), table_name='message_logs')
    op.drop_index(op.f('ix_message_logs_channel'), table_name='message_logs')
    op.drop_index(op.f('ix_message_logs_lead_id'), table_name='message_logs')
    op.drop_index(op.f('ix_message_logs_id'), table_name='message_logs')
    op.drop_table('message_logs')
    
    op.drop_index(op.f('ix_workflow_executions_status'), table_name='workflow_executions')
    op.drop_index(op.f('ix_workflow_executions_lead_id'), table_name='workflow_executions')
    op.drop_index(op.f('ix_workflow_executions_workflow_id'), table_name='workflow_executions')
    op.drop_index(op.f('ix_workflow_executions_id'), table_name='workflow_executions')
    op.drop_table('workflow_executions')
    
    op.drop_index(op.f('ix_workflow_steps_workflow_id'), table_name='workflow_steps')
    op.drop_index(op.f('ix_workflow_steps_id'), table_name='workflow_steps')
    op.drop_table('workflow_steps')
    
    op.drop_index(op.f('ix_marketing_workflows_status'), table_name='marketing_workflows')
    op.drop_index(op.f('ix_marketing_workflows_name'), table_name='marketing_workflows')
    op.drop_index(op.f('ix_marketing_workflows_id'), table_name='marketing_workflows')
    op.drop_table('marketing_workflows')
    
    op.drop_index(op.f('ix_communication_templates_category'), table_name='communication_templates')
    op.drop_index(op.f('ix_communication_templates_channel'), table_name='communication_templates')
    op.drop_index(op.f('ix_communication_templates_name'), table_name='communication_templates')
    op.drop_index(op.f('ix_communication_templates_id'), table_name='communication_templates')
    op.drop_table('communication_templates')
