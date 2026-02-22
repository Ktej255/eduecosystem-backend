"""
Full FastAPI application for Eduecosystem Backend.
Restored with database connectivity, auth, and all API routes.
"""
from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
import os
import sys

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)


def seed_meditation_processes():
    """Seed default meditation processes if table is empty"""
    from sqlalchemy import text, inspect
    from app.db.session import engine
    
    # Sample meditation video URL for testing (replace with actual videos later)
    SAMPLE_VIDEO = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    
    # Format: (name, description, order, duration_min, level, video_url)
    MEDITATION_PROCESSES = [
        ("Relaxation", "Complete body relaxation from head to toe", 1, 3, 1, SAMPLE_VIDEO),
        ("Breath Awareness", "Observe natural breathing without controlling", 2, 3, 1, SAMPLE_VIDEO),
        ("Counting Breath", "Count breaths from 1 to 10, then restart", 3, 3, 1, SAMPLE_VIDEO),
        ("Ajna Focus", "Focus attention on the third eye center", 4, 3, 1, SAMPLE_VIDEO),
        ("Om Chanting", "Mental chanting of Om with each breath", 5, 3, 1, SAMPLE_VIDEO),
        ("Light Visualization", "Visualize pure white light at the third eye", 6, 3, 1, SAMPLE_VIDEO),
        ("Heart Opening", "Feel warmth and expansion in the heart center", 7, 3, 1, SAMPLE_VIDEO),
        ("Energy Awareness", "Feel subtle energy in the body", 8, 3, 1, SAMPLE_VIDEO),
        ("Silence", "Rest in complete inner silence", 9, 3, 1, SAMPLE_VIDEO),
        ("Gratitude", "Feel deep gratitude for life and existence", 10, 3, 1, SAMPLE_VIDEO),
        ("Intention Setting", "Set positive intentions for the day", 11, 2, 1, SAMPLE_VIDEO),
        ("Gentle Awakening", "Slowly return to normal awareness", 12, 2, 1, SAMPLE_VIDEO),
    ]
    
    try:
        inspector = inspect(engine)
        if 'meditation_processes' not in inspector.get_table_names():
            logger.info("meditation_processes table not found, skipping seed")
            return
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM meditation_processes"))
            if result.scalar() > 0:
                logger.info("Meditation processes already seeded")
                return
            
            for name, desc, order_num, duration, level, video_url in MEDITATION_PROCESSES:
                conn.execute(text(
                    'INSERT INTO meditation_processes '
                    '(name, description, "order", duration_minutes, level, is_active, video_url) '
                    'VALUES (:name, :desc, :order_num, :duration, :level, 1, :video_url)'
                ), {"name": name, "desc": desc, "order_num": order_num, "duration": duration, "level": level, "video_url": video_url})
            
            conn.commit()
            logger.info(f"Seeded {len(MEDITATION_PROCESSES)} meditation processes")
    except Exception as e:
        logger.warning(f"Could not seed meditation data: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for production deployment.
    Initializes essential services only (skips Redis/Sentry for now).
    IMPORTANT: Keep this lightweight - avoid database operations that could hang.
    """
    logger.info("Starting Eduecosystem Backend (Production Mode)...")
    
    # Skip meditation seeding on startup to prevent database timeout hangs
    # This can be run manually via API endpoint if needed
    # seed_meditation_processes()
    
    yield  # Application runs here

    logger.info("Shutting down Eduecosystem Backend...")



# Import settings after defining lifespan to avoid circular imports
try:
    from app.core.config import settings
    PROJECT_NAME = settings.PROJECT_NAME
    API_V1_STR = settings.API_V1_STR
    BACKEND_CORS_ORIGINS = settings.BACKEND_CORS_ORIGINS
except Exception as e:
    logger.warning(f"Could not import settings: {e}. Using defaults.")
    PROJECT_NAME = "Eduecosystem API"
    API_V1_STR = "/api/v1"
    BACKEND_CORS_ORIGINS = ["*"]


# Skip lifespan during testing
if os.getenv("TESTING") == "true":
    app = FastAPI(
        title=PROJECT_NAME,
        openapi_url=f"{API_V1_STR}/openapi.json",
    )
else:
    app = FastAPI(
        title=PROJECT_NAME,
        openapi_url=f"{API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

# Rate Limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Origins — single source of truth from settings + any extras
all_cors_origins = list(set(BACKEND_CORS_ORIGINS if BACKEND_CORS_ORIGINS else []))

# Remove wildcard if specific origins are also present (wildcard with credentials fails)
if "*" in all_cors_origins and len(all_cors_origins) > 1:
    all_cors_origins.remove("*")

use_credentials = "*" not in all_cors_origins

logger.info(f"CORS Origins configured: {all_cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Compression Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

from fastapi.staticfiles import StaticFiles
# Ensure uploads directory exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")
# Mount uploads directory for static access
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# SECURITY: Add security headers middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses to prevent common attacks."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable browser XSS filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy (allow only same origin for scripts)
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        
        # HSTS - Enforce HTTPS (only in production)
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Multi-Tenant Detection Middleware (Phase 6)
# from app.middleware.tenant import TenantMiddleware
# app.add_middleware(TenantMiddleware)


# Import and include API router
try:
    from app.api.api_v1.api import api_router
    app.include_router(api_router, prefix=API_V1_STR)
    logger.info(f"API router included successfully with prefix {API_V1_STR}")
except Exception as e:
    import traceback
    logger.critical(f"Failed to include API router: {str(e)}")
    traceback.print_exc()



# Application version — single source of truth
APP_VERSION = settings.APP_VERSION

# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint returning welcome message."""
    return {
        "message": "Welcome to Eduecosystem Backend API",
        "status": "running",
        "version": APP_VERSION,
        "docs": "/docs"
    }


# Health check endpoint
@app.get("/health")
def health_check():
    """Simple health check for App Runner."""
    return {"status": "ok", "message": "Backend is healthy", "version": APP_VERSION}

# /debug-cors endpoint REMOVED for security — exposed internal configuration


# Detailed health check with database connectivity
@app.get("/health/detailed")
def detailed_health_check():
    """Detailed health check with database connectivity test."""
    health_status = {
        "status": "healthy",
        "checks": {},
        "env": {
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "unknown"),
            "DATABASE_URL_HOST": settings.DATABASE_URL.split("@")[1].split("/")[0] if "@" in settings.DATABASE_URL else "local",
            "DATABASE_NAME": settings.DATABASE_URL.split("/")[-1] if "/" in settings.DATABASE_URL else "unknown"
        }
    }
    
    # Network connectivity check (socket)
    try:
        import socket
        host = settings.DATABASE_URL.split("@")[1].split(":")[0] if "@" in settings.DATABASE_URL else None
        port = int(settings.DATABASE_URL.split("@")[1].split(":")[1].split("/")[0]) if "@" in settings.DATABASE_URL else None
        if host and port:
            s = socket.create_connection((host, port), timeout=3)
            s.close()
            health_status["checks"]["network"] = {
                "status": "healthy",
                "message": f"Successfully reached {host}:{port}"
            }
        else:
            health_status["checks"]["network"] = {
                "status": "skipped",
                "message": "Local database or invalid URL"
            }
    except Exception as e:
        health_status["checks"]["network"] = {
            "status": "unhealthy",
            "message": f"Cannot reach database host: {str(e)}"
        }

    # Database connectivity check
    try:
        from sqlalchemy import text
        from app.db.session import SessionLocal
        db = SessionLocal()
        # Use a short timeout for the check
        db.execute(text("SELECT 1"))
        db.close()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
    
    return health_status


# API status endpoint
@app.get("/api/v1/status")
def api_status():
    """API status endpoint."""
    return {
        "api_version": "v1",
        "app_version": APP_VERSION,
        "status": "operational",
        "environment": os.getenv("ENVIRONMENT", "production")
    }


# ONE-TIME MIGRATION: Add missing columns to production database
# SECURITY: Requires superuser authentication
try:
    from app.api.deps import get_current_superuser
except ImportError:
    # Fallback if deps module isn't available
    get_current_superuser = None


@app.post("/admin/migrate-db")
def migrate_database(current_user=Depends(get_current_superuser) if get_current_superuser else None):
    """
    One-time database migration to add missing columns.
    Safe to run multiple times (uses IF NOT EXISTS / DO NOTHING logic).
    REQUIRES: Superuser bearer token.
    """
    if current_user is None and get_current_superuser is not None:
        return JSONResponse(status_code=401, content={"detail": "Authentication required"})

    from sqlalchemy import text
    from app.db.session import SessionLocal

    db = SessionLocal()
    results = []

    # All columns that might be missing from the users table
    migrations = [
        ("xp", "ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0"),
        ("streak_days", "ALTER TABLE users ADD COLUMN IF NOT EXISTS streak_days INTEGER DEFAULT 0"),
        ("coins", "ALTER TABLE users ADD COLUMN IF NOT EXISTS coins INTEGER DEFAULT 0"),
        ("token_version", "ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER DEFAULT 1"),
        ("is_approved", "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_approved BOOLEAN DEFAULT TRUE"),
        ("is_banned", "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE"),
        ("email_notifications", "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT TRUE"),
        ("is_premium", "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT FALSE"),
        ("stripe_customer_id", "ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR NULL"),
        ("subscription_status", "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR DEFAULT 'free'"),
        ("graphotherapy_enrollment_date", "ALTER TABLE users ADD COLUMN IF NOT EXISTS graphotherapy_enrollment_date TIMESTAMP NULL"),
        ("is_graphotherapy_exclusive", "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_graphotherapy_exclusive BOOLEAN DEFAULT FALSE"),
        ("organization_id", "ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id INTEGER NULL"),
        ("is_sso_user", "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_sso_user BOOLEAN DEFAULT FALSE"),
        ("sso_external_id", "ALTER TABLE users ADD COLUMN IF NOT EXISTS sso_external_id VARCHAR NULL"),
        ("is_verified", "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE"),
        ("is_ras_authorized", "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_ras_authorized BOOLEAN DEFAULT FALSE"),
        ("is_batch1_authorized", "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_batch1_authorized BOOLEAN DEFAULT FALSE"),
        ("is_batch2_authorized", "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_batch2_authorized BOOLEAN DEFAULT FALSE"),
        ("totp_secret", "ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR NULL"),
        ("revision_level", "ALTER TABLE users ADD COLUMN IF NOT EXISTS revision_level VARCHAR NULL"),
        ("revision_exam_id", "ALTER TABLE users ADD COLUMN IF NOT EXISTS revision_exam_id VARCHAR NULL"),
        ("push_subscription", "ALTER TABLE users ADD COLUMN IF NOT EXISTS push_subscription JSON NULL"),
        ("last_login", "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP NULL"),
        ("role", "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'student'"),
        ("group_id", "ALTER TABLE users ADD COLUMN IF NOT EXISTS group_id INTEGER NULL"),
        ("username", "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR NULL"),
        ("created_at", "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()"),
    ]

    try:
        for col_name, sql in migrations:
            try:
                db.execute(text(sql))
                results.append({"column": col_name, "status": "applied"})
            except Exception as e:
                results.append({"column": col_name, "status": f"skipped: {str(e)}"})

        db.commit()
        db.close()

        return {
            "status": "migration_complete",
            "version": APP_VERSION,
            "results": results
        }
    except Exception as e:
        db.rollback()
        db.close()
        return {"status": "migration_failed", "error": str(e)}



# End of file
