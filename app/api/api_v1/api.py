from fastapi import APIRouter
from app.api.api_v1.endpoints import (
    auth,
    users,
    # tasks,
    # ... (all other imports commented out)
    admin_drill,
    drill,
    daily_actions,
    graphotherapy,
    meditation,
    admin_meditation,
    prelims_recall,
    batch1_content,
    ai_debug,
    ai,
    custom_planner,
)

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router, prefix="/login", tags=["login"])

# Users
api_router.include_router(users.router, prefix="/users", tags=["users"])

# AI Chat (for chat widget)
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])

# Drill System (Admin)
api_router.include_router(admin_drill.router, prefix="/admin/drill", tags=["admin-drill"])

# Drill System (Student)
api_router.include_router(drill.router, prefix="/drill", tags=["drill"])

# Daily Action
api_router.include_router(daily_actions.daily_router, prefix="/daily-actions", tags=["daily-actions"])

# Graphotherapy
api_router.include_router(graphotherapy.router, prefix="/graphotherapy", tags=["graphotherapy"])

# Meditation (Student)
api_router.include_router(meditation.router, prefix="/meditation", tags=["meditation"])

# Meditation (Admin)
api_router.include_router(admin_meditation.router, prefix="/admin/meditation", tags=["admin-meditation"])

# Prelims Recall Analysis
api_router.include_router(prelims_recall.router, prefix="/prelims", tags=["prelims"])

# Batch 1 Content (Videos/Segments)
api_router.include_router(batch1_content.router, prefix="/batch1", tags=["batch1"])

# AI Debug (Teacher Portal Transparency Dashboard)
api_router.include_router(ai_debug.router, prefix="/ai-debug", tags=["ai-debug"])

# Leads Management
from app.api.api_v1.endpoints import leads
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])

# Mobile CRM - Field Activities
from app.api.api_v1.endpoints import field_activities
api_router.include_router(field_activities.router, prefix="/field-activities", tags=["field-activities"])

# Mobile CRM - Call Logs
from app.api.api_v1.endpoints import call_logs
api_router.include_router(call_logs.router, prefix="/call-logs", tags=["call-logs"])

# Mobile CRM - Voice Notes
from app.api.api_v1.endpoints import voice_notes
api_router.include_router(voice_notes.router, prefix="/voice-notes", tags=["voice-notes"])

# Advanced User Management
from app.api.api_v1.endpoints import user_management
api_router.include_router(user_management.router, prefix="/admin/user-management", tags=["user-management"])

# Marketing Automation
from app.api.api_v1.endpoints import marketing_automation
api_router.include_router(marketing_automation.router, prefix="/marketing-automation", tags=["marketing-automation"])

# Retention System (FSRS-based knowledge decay tracking)
from app.api.api_v1.endpoints import retention
api_router.include_router(retention.router, prefix="/retention", tags=["retention"])

# Custom Planner (RAS Revision)
api_router.include_router(custom_planner.router, prefix="/planner", tags=["planner"])
