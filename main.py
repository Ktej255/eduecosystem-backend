"""
Full FastAPI application for Eduecosystem Backend.
Restored with database connectivity, auth, and all API routes.
"""
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
import os
import sys

from fastapi import Request
from fastapi.responses import JSONResponse

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
    """
    logger.info("Starting Eduecosystem Backend (Production Mode)...")
    
    # Auto-seed meditation processes if table is empty
    seed_meditation_processes()
    
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

# Set all CORS enabled origins
if BACKEND_CORS_ORIGINS:
    # If using credentials, we cannot use "*" for allow_origins.
    # We must either list specific origins or handle it dynamically.
    # For now, if "*" is provided, we set allow_credentials to False.
    use_credentials = True
    origins = [str(origin) for origin in BACKEND_CORS_ORIGINS]
    
    if "*" in origins:
        use_credentials = False
        
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=use_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Compression Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Import and include API router
try:
    print("Attempting to import api_router...")
    from app.api.api_v1.api import api_router
    print(f"api_router imported successfully, routes: {len(api_router.routes)}")
    app.include_router(api_router, prefix=API_V1_STR)
    print("API router included successfully")
    logger.info("API router included successfully")
except Exception as e:
    import traceback
    print(f"FAILED to include API router: {e}")
    print(traceback.format_exc())
    logger.error(f"Failed to include API router: {e}")



# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint returning welcome message."""
    return {
        "message": "Welcome to Eduecosystem Backend API",
        "status": "running",
        "version": "1.0.2",
        "docs": "/docs"
    }


# Health check endpoint
@app.get("/health")
def health_check():
    """Simple health check for App Runner."""
    return {"status": "ok", "message": "Backend is healthy"}


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
        "status": "operational",
        "environment": os.getenv("ENVIRONMENT", "production")
    }



# End of file
