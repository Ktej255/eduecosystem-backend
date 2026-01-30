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
    certificates,
    categories,
    courses,
    notes,
    announcements,
    discussions,
    live_classes,
    learning_paths,
    peer_reviews,
    order,
    reviews,
    subscriptions,
    progress,
    quizzes,
    assignments,
)



api_router = APIRouter()

# Authentication
api_router.include_router(auth.router, prefix="/login", tags=["login"])
from app.api.api_v1.endpoints import auth_2fa
api_router.include_router(auth_2fa.router, prefix="/2fa", tags=["2fa"])

# Users
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Admin (Stats, Users Management, Logs)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(retention.router, prefix="/retention", tags=["retention"])
api_router.include_router(graphotherapy.router, prefix="/graphotherapy", tags=["graphotherapy"])

# Grapho Upload (Handwriting Analysis)
from app.api.api_v1.endpoints import grapho
api_router.include_router(grapho.router, prefix="/grapho", tags=["grapho"])

# Daily Actions (Tasks, Habits, Reflection)
api_router.include_router(daily_actions.daily_router, prefix="/daily-actions", tags=["daily-actions"])

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
# from app.api.api_v1.endpoints import retention
# api_router.include_router(retention.router, prefix="/retention", tags=["retention"])

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

# Productivity (Daily Briefing, News Quiz)
from app.api.api_v1.endpoints import productivity
api_router.include_router(productivity.router, prefix="/productivity", tags=["productivity"])

# Community (Virtual Library, Presence, Leaderboard)
from app.api.api_v1.endpoints import community
api_router.include_router(community.router, prefix="/community", tags=["community"])

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


# Adaptive Learning (Dynamic Knowledge Graph & BKT)
from app.api.api_v1.endpoints import adaptive_learning
api_router.include_router(adaptive_learning.router, prefix="/adaptive-learning", tags=["adaptive-learning"])

# Anti-Gravity Phase-Wise Roadmap
from app.api.api_v1.endpoints import antigravity
api_router.include_router(antigravity.router, prefix="/antigravity", tags=["antigravity"])

# Certificates
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])

# Courses and Categories
api_router.include_router(categories.router, prefix="/courses/categories", tags=["categories"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])

# Learning Paths
from app.api.api_v1.endpoints import learning_paths
api_router.include_router(learning_paths.router, prefix="/learning-paths", tags=["learning-paths"])

# Student Notes and Bookmarks
from app.api.api_v1.endpoints import notes
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])

# Announcements
from app.api.api_v1.endpoints import announcements
api_router.include_router(announcements.router, prefix="/announcements", tags=["announcements"])

# Discussions
from app.api.api_v1.endpoints import discussions
api_router.include_router(discussions.router, prefix="/discussions", tags=["discussions"])

# Live Classes
from app.api.api_v1.endpoints import live_classes
api_router.include_router(live_classes.router, prefix="/live-classes", tags=["live-classes"])

# Orders
from app.api.api_v1.endpoints import order
api_router.include_router(order.router, prefix="/orders", tags=["orders"])

# Cart
from app.api.api_v1.endpoints import cart
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])

# Groups
from app.api.api_v1.endpoints import groups
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])

# Shadow Mode
from app.api.api_v1.endpoints import shadow_mode
api_router.include_router(shadow_mode.router, prefix="/shadow-mode", tags=["shadow-mode"])

# Peer Reviews
from app.api.api_v1.endpoints import peer_reviews
api_router.include_router(peer_reviews.router, prefix="/peer-reviews", tags=["peer-reviews"])

# Question Banks
from app.api.api_v1.endpoints import question_banks
api_router.include_router(question_banks.router, prefix="/question-banks", tags=["question-banks"])

# LMS (comprehensive endpoints)
from app.api.api_v1.endpoints import lms
api_router.include_router(lms.router, prefix="/lms", tags=["lms"])

# Collaborative Projects
from app.api.api_v1.endpoints import collaborative_projects
api_router.include_router(collaborative_projects.router, prefix="/projects", tags=["collaborative-projects"])

# Certificate Templates
from app.api.api_v1.endpoints import certificate_templates
api_router.include_router(certificate_templates.router, prefix="/certificate-templates", tags=["certificate-templates"])

# Tutor (AI)
from app.api.api_v1.endpoints import tutor
api_router.include_router(tutor.router, prefix="/tutor", tags=["tutor"])

# Email Notifications
from app.api.api_v1.endpoints import email_notifications
api_router.include_router(email_notifications.router, prefix="/email-notifications", tags=["email-notifications"])

# Monitoring
from app.api.api_v1.endpoints import monitoring
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])

# Learning Groups
from app.api.api_v1.endpoints import learning_groups
api_router.include_router(learning_groups.router, prefix="/learning-groups", tags=["learning-groups"])

# Enterprise SSO
from app.api.api_v1.endpoints import sso
api_router.include_router(sso.router, prefix="/sso", tags=["sso"])




# Course Reviews
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])

# Subscriptions
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])

# Lesson Progress
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])

# Quizzes
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["quizzes"])

# Assignments
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])

# Modules and Lessons (from courses)
api_router.include_router(courses.modules_router, prefix="/modules", tags=["modules"])
api_router.include_router(courses.lessons_router, prefix="/lessons", tags=["lessons"])

# User Activities (Generic Progress Tracking)
from app.api.api_v1.endpoints import user_activities
api_router.include_router(user_activities.router, prefix="/user-activities", tags=["user-activities"])
