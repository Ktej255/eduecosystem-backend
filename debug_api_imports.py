import sys
import os

sys.path.append(os.getcwd())

modules = [
    "auth",
    "users",
    "tasks",
    "grapho",
    "meditation",
    "gamification",
    "analytics",
    "groups",
    "lms",
    "monitoring",
    "community",
    "ai",
    "shadow_mode",
    "notifications",
    "recommendations",
    "social",
    "verification",
    "admin",
    "courses",
    "progress",
    "certificates",
    "ai_course",
    "upload",
    "lesson_drip",
    "categories",
    "bundles",
    "quizzes",
    "quiz_management",
    "assignments",
    "discussions",
    "announcements",
    "notes",
    "question_banks",
    "peer_reviews",
    "live_classes",
    "learning_paths",
    "certificate_templates",
    "chat",
    "live_class_interactive",
    "health",
    "reviews",
    "email_notifications",
    "achievements",
    "challenges",
    "course_payment",
    "coupons",
    "collaborative_projects",
    "translation",
    "marketplace",
    "subscriptions",
    "affiliates",
    "ai_tools",
    "sso",
    "cart",
    "order",
    "invoices",
    "revenue_analytics",
    "reports",
    "payment_methods",
    "guest_checkout",
    "comparison_analytics",
    "cohort_analytics",
    "executive_analytics",
    "tutor",
    "tax",
    "two_factor",
    "stripe_webhooks",
    "exports",
    "learning_groups",
]

print("Starting import check...")
for module in modules:
    try:
        print(f"Importing app.api.api_v1.endpoints.{module}...", end="", flush=True)
        __import__(f"app.api.api_v1.endpoints.{module}")
        print(" OK")
    except Exception as e:
        print(f" FAILED: {e}")
    except KeyboardInterrupt:
        print(f" HANG DETECTED at {module}")
        sys.exit(1)

print("All imports checked.")
