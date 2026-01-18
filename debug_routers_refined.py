import sys
import os

# Add backend to path
sys.path.append('backend')

from fastapi import APIRouter
import fastapi
import traceback

def test_router(module_name):
    try:
        print(f"Testing {module_name}...", end=" ", flush=True)
        # Import inside the function to isolate
        exec(f"from app.api.api_v1.endpoints import {module_name} as module")
        import app.api.api_v1.endpoints
        module = getattr(sys.modules['app.api.api_v1.endpoints'], module_name)
        
        main_router = APIRouter()
        if hasattr(module, "router"):
             main_router.include_router(module.router)
        elif hasattr(module, "daily_router"):
             main_router.include_router(module.daily_router)
        print("OK")
        return True
    except Exception as e:
        print("FAILED")
        print("-" * 40)
        traceback.print_exc()
        print("-" * 40)
        return False

# Manual list of modules to avoid import complexity
modules = [
    "auth", "users", "admin", "admin_drill", "drill", "daily_actions",
    "graphotherapy", "meditation", "admin_meditation", "prelims_recall",
    "batch1_content", "batch1_tests", "ai_debug", "ai", "pdf_study", "retention",
    "leads", "field_activities", "call_logs", "voice_notes", "user_management",
    "marketing_automation", "ai_learning", "planner", "ai_tools", "ai_course",
    "ai_avatars", "flashcards", "audio_analysis", "packs", "knowledge_graph",
    "study", "polity", "attendance", "branding", "admin_organizations",
    "funnel_leads", "funnel_analysis", "premium_analysis", "advanced_health_analysis",
    "mains_evaluation", "development_history", "pdr", "community", "productivity",
    "gamification", "voice_tutor", "grapho_vision", "analytics", "commerce", "b2b",
    "notifications", "admin_sentiment", "admin_security", "admin_nudges",
    "admin_student_activity", "instructor_analytics", "ai_tutor", "pack_battles"
]

for m in modules:
    if not test_router(m):
        sys.exit(1)

print("\nAll routers are valid!")
