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

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for production deployment.
    Initializes essential services only (skips Redis/Sentry for now).
    """
    logger.info("Starting Eduecosystem Backend (Production Mode)...")
    
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
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
        "version": "1.0.0",
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
        "checks": {}
    }
    
    # Database connectivity check
    try:
        from sqlalchemy import text
        from app.db.session import SessionLocal
        db = SessionLocal()
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
