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

# Streak & Engagement System
from app.api.api_v1.endpoints import streak
api_router.include_router(streak.router, prefix="/streak", tags=["streak"])

# Engagement Features (Connect The Dots, Daily Wisdom)
from app.api.api_v1.endpoints import engagement
api_router.include_router(engagement.router, prefix="/engagement", tags=["engagement"])

# Habit Tracking System
from app.api.api_v1.endpoints import habits
api_router.include_router(habits.router, prefix="/habits", tags=["habits"])

# Mastery Level System
from app.api.api_v1.endpoints import mastery
api_router.include_router(mastery.router, prefix="/mastery", tags=["mastery"])

# Video Management (LMS)
from app.api.api_v1.endpoints import videos
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])

# Content Generator (AI Flashcards & MCQs)
from app.api.api_v1.endpoints import content_generator
api_router.include_router(content_generator.router, prefix="/generate", tags=["content-generator"])

# Audio Analysis (Voice Recording Analysis)
from app.api.api_v1.endpoints import audio_analysis
api_router.include_router(audio_analysis.router, prefix="/audio", tags=["audio-analysis"])

# Progress Tracking (CSAT & Evening Sessions)
from app.api.api_v1.endpoints import session_progress
api_router.include_router(session_progress.router, prefix="/session-progress", tags=["session-progress"])

# Custom Study Planner (RAS Dynamic Planner)
from app.api.api_v1.endpoints import custom_planner
api_router.include_router(custom_planner.router, prefix="/planner", tags=["custom-planner"])

