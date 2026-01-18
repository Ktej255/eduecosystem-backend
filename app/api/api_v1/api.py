from fastapi import APIRouter
from app.api.api_v1.endpoints import (
    auth,
    users,
    admin,
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
    batch1_tests,
    ai_debug,
    ai,
    pdf_study,
    retention,
)


api_router = APIRouter()

# Authentication
api_router.include_router(auth.router, prefix="/login", tags=["login"])
from app.api.api_v1.endpoints import auth_2fa
api_router.include_router(auth_2fa.router, prefix="/2fa", tags=["2fa"])

# Users
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(retention.router, prefix="/retention", tags=["retention"])

# Admin (User Management)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

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

# Batch 1 Test Results
api_router.include_router(batch1_tests.router, prefix="/batch1", tags=["batch1-tests"])

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

# AI Learning (MCQ Generator, Coaching)
from app.api.api_v1.endpoints import ai_learning
api_router.include_router(ai_learning.router, prefix="/ai-learning", tags=["ai-learning"])

# RAS Revision Planner (40-Day Plan)
from app.api.api_v1.endpoints import planner
api_router.include_router(planner.router, prefix="/planner", tags=["planner"])

# AI Tools (Essay Grading, Quiz Generation, Difficulty Analysis, Plagiarism Detection)
from app.api.api_v1.endpoints import ai_tools
api_router.include_router(ai_tools.router, prefix="/ai-tools", tags=["ai-tools"])

# AI Course Generation
from app.api.api_v1.endpoints import ai_course
api_router.include_router(ai_course.router, prefix="/ai-course", tags=["ai-course"])

# AI Avatars
from app.api.api_v1.endpoints import ai_avatars
api_router.include_router(ai_avatars.router, prefix="/ai-avatars", tags=["ai-avatars"])

# Flashcards (AI-driven spaced repetition)
from app.api.api_v1.endpoints import flashcards
api_router.include_router(flashcards.router, prefix="/flashcards", tags=["flashcards"])

# Audio Analysis (Flashcard Recall)
from app.api.api_v1.endpoints import audio_analysis
api_router.include_router(audio_analysis.router, prefix="/audio-analysis", tags=["audio-analysis"])

# Wolf Packs (Competitive Study Groups)
from app.api.api_v1.endpoints import packs
api_router.include_router(packs.router, prefix="/packs", tags=["packs"])

# Knowledge Graph (Interactive Syllabus Explorer)
from app.api.api_v1.endpoints import knowledge_graph
api_router.include_router(knowledge_graph.router, prefix="/knowledge-graph", tags=["knowledge-graph"])

# PDF Study (Self-Study Mode for Batch 1)
api_router.include_router(pdf_study.router, prefix="/pdf-study", tags=["pdf-study"])

# Study Sessions (Pomodoro, Revision)
from app.api.api_v1.endpoints import study
api_router.include_router(study.router, prefix="/study", tags=["study"])

# Polity Chapter Tracker
from app.api.api_v1.endpoints import polity
api_router.include_router(polity.router, prefix="/polity", tags=["polity"])

# Attendance Tracking
from app.api.api_v1.endpoints import attendance
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])

# Public Branding (Multi-Tenancy Phase 6)
from app.api.api_v1.endpoints import branding
api_router.include_router(branding.router, prefix="/public", tags=["branding"])

# Admin Organizations Management (Multi-Tenancy Phase 7)
from app.api.api_v1.endpoints import admin_organizations
api_router.include_router(admin_organizations.router, prefix="/admin", tags=["admin-organizations"])

# Graphotherapy Funnel Leads
from app.api.api_v1.endpoints import funnel_leads
api_router.include_router(funnel_leads.router, prefix="/leads", tags=["funnel-leads"])

# Graphotherapy Analysis (AI)
from app.api.api_v1.endpoints import funnel_analysis
api_router.include_router(funnel_analysis.router, prefix="/funnel", tags=["funnel-analysis"])

# Premium Analysis (AI)
from app.api.api_v1.endpoints import premium_analysis
api_router.include_router(premium_analysis.router, prefix="/funnel", tags=["premium-analysis"])

# Advanced Health Analysis (Level 3)
from app.api.api_v1.endpoints import advanced_health_analysis
api_router.include_router(advanced_health_analysis.router, prefix="/graphotherapy", tags=["health-analysis"])

# Mains Answer Evaluation (AI)
from app.api.api_v1.endpoints import mains_evaluation
api_router.include_router(mains_evaluation.router, prefix="/mains", tags=["mains-evaluation"])

# Development History and Daily Reports (Admin Portal)
from app.api.api_v1.endpoints import development_history
api_router.include_router(development_history.router, prefix="/admin", tags=["development-history"])

# Portal Map (PDR)
from app.api.api_v1.endpoints import pdr
api_router.include_router(pdr.router, prefix="/admin", tags=["pdr"])

# Community (Silence Library, Leaderboards)
from app.api.api_v1.endpoints import community
api_router.include_router(community.router, prefix="/community", tags=["community"])

# Productivity (News Quiz)
from app.api.api_v1.endpoints import productivity
api_router.include_router(productivity.router, prefix="/productivity", tags=["productivity"])

# Gamification (Sadhana Streaks)
from app.api.api_v1.endpoints import gamification
api_router.include_router(gamification.router, prefix="/gamification", tags=["gamification"])

# Voice of Wisdom (AI Tutor)
from app.api.api_v1.endpoints import voice_tutor
api_router.include_router(voice_tutor.router, prefix="/voice-tutor", tags=["voice-tutor"])

# Holographic Graphotherapy (Vision AI)
from app.api.api_v1.endpoints import grapho_vision
api_router.include_router(grapho_vision.router, prefix="/grapho-vision", tags=["grapho-vision"])

# Predictive Analytics (Admin)
from app.api.api_v1.endpoints import analytics
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# Commerce (Smart Bundles)
from app.api.api_v1.endpoints import commerce
api_router.include_router(commerce.router, prefix="/commerce", tags=["commerce"])

# B2B (Corporate Portal)
from app.api.api_v1.endpoints import b2b
api_router.include_router(b2b.router, prefix="/b2b", tags=["b2b"])

# Notifications (Nudge)
from app.api.api_v1.endpoints import notifications
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Admin Sentiment (Mindscape Dash)
from app.api.api_v1.endpoints import admin_sentiment
api_router.include_router(admin_sentiment.router, prefix="/admin/sentiment", tags=["admin-sentiment"])

# Admin Security (Ghost Login Detection)
from app.api.api_v1.endpoints import admin_security
api_router.include_router(admin_security.router, prefix="/admin/security", tags=["admin-security"])

# Admin Nudges (Retention Automation)
from app.api.api_v1.endpoints import admin_nudges
api_router.include_router(admin_nudges.router, prefix="/admin/nudges", tags=["admin-nudges"])

# Admin Student Activity (High Resolution Tracking)
from app.api.api_v1.endpoints import admin_student_activity
api_router.include_router(admin_student_activity.router, prefix="/admin/student-activity", tags=["admin-student-activity"])


# Instructor Analytics (Unified)
from app.api.api_v1.endpoints import instructor_analytics
api_router.include_router(instructor_analytics.router, prefix="/instructor/analytics", tags=["instructor-analytics"])


# AI Tutor (RAG Chat)
from app.api.api_v1.endpoints import ai_tutor
api_router.include_router(ai_tutor.router, prefix="/ai/tutor", tags=["ai-tutor"])

# Pack Battles (PvP)
from app.api.api_v1.endpoints import pack_battles
api_router.include_router(pack_battles.router, prefix="/pack-battles", tags=["pack-battles"])


