import sys
import os

# Add backend to path
sys.path.append('backend')

from fastapi import APIRouter
from app.api.api_v1.endpoints import (
    auth, users, admin, admin_drill, drill, daily_actions,
    graphotherapy, meditation, admin_meditation, prelims_recall,
    batch1_content, batch1_tests, ai_debug, ai, pdf_study, retention,
    leads, field_activities, call_logs, voice_notes, user_management,
    marketing_automation, ai_learning, planner, ai_tools, ai_course,
    ai_avatars, flashcards, audio_analysis, packs, knowledge_graph,
    study, polity, attendance, branding, admin_organizations,
    funnel_leads, funnel_analysis, premium_analysis, advanced_health_analysis,
    mains_evaluation, development_history, pdr, community, productivity,
    gamification, voice_tutor, grapho_vision, analytics, commerce, b2b,
    notifications, admin_sentiment, admin_security, admin_nudges,
    admin_student_activity, instructor_analytics, ai_tutor, pack_battles
)

routers = [
    (auth, "auth"), (users, "users"), (admin, "admin"), (admin_drill, "admin_drill"),
    (drill, "drill"), (daily_actions, "daily_actions"), (graphotherapy, "graphotherapy"),
    (meditation, "meditation"), (admin_meditation, "admin_meditation"),
    (prelims_recall, "prelims_recall"), (batch1_content, "batch1_content"),
    (batch1_tests, "batch1_tests"), (ai_debug, "ai_debug"), (ai, "ai"),
    (pdf_study, "pdf_study"), (retention, "retention"), (leads, "leads"),
    (field_activities, "field_activities"), (call_logs, "call_logs"),
    (voice_notes, "voice_notes"), (user_management, "user_management"),
    (marketing_automation, "marketing_automation"), (ai_learning, "ai_learning"),
    (planner, "planner"), (ai_tools, "ai_tools"), (ai_course, "ai_course"),
    (ai_avatars, "ai_avatars"), (flashcards, "flashcards"), (audio_analysis, "audio_analysis"),
    (packs, "packs"), (knowledge_graph, "knowledge_graph"), (study, "study"),
    (polity, "polity"), (attendance, "attendance"), (branding, "branding"),
    (admin_organizations, "admin_organizations"), (funnel_leads, "funnel_leads"),
    (funnel_analysis, "funnel_analysis"), (premium_analysis, "premium_analysis"),
    (advanced_health_analysis, "advanced_health_analysis"), (mains_evaluation, "mains_evaluation"),
    (development_history, "development_history"), (pdr, "pdr"), (community, "community"),
    (productivity, "productivity"), (gamification, "gamification"), (voice_tutor, "voice_tutor"),
    (grapho_vision, "grapho_vision"), (analytics, "analytics"), (commerce, "commerce"),
    (b2b, "b2b"), (notifications, "notifications"), (admin_sentiment, "admin_sentiment"),
    (admin_security, "admin_security"), (admin_nudges, "admin_nudges"),
    (admin_student_activity, "admin_student_activity"), (instructor_analytics, "instructor_analytics"),
    (ai_tutor, "ai_tutor"), (pack_battles, "pack_battles")
]

main_router = APIRouter()

for module, name in routers:
    try:
        print(f"Testing {name}...")
        # Access router.routes to trigger validation if possible
        if hasattr(module, "router"):
             main_router.include_router(module.router)
        elif hasattr(module, "daily_router"):
             main_router.include_router(module.daily_router)
        print(f"  {name} OK")
    except Exception as e:
        print(f"  {name} FAILED: {e}")
        import traceback
        traceback.print_exc()
        # sys.exit(1) # Continue to find more if needed
