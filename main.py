import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.db.session import SessionLocal

# Setup logging
logger.add("logs/backend.log", rotation="500 MB", level="INFO")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Create DB connection
    logger.info("Starting up backend services...")
    yield
    # Shutdown: Close DB connection
    logger.info("Shutting down backend services...")

# Initialize FastAPI
PROJECT_NAME = "EduEcosystem API"
API_V1_STR = "/api/v1"


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

# Define base CORS origins for production
all_cors_origins = [
    "https://sarit-graphotherapy-frontend-503001969959.us-central1.run.app",
    "https://eduecosystem-frontend-503001969959.us-central1.run.app",
    "https://eduecosystem-frontend.vercel.app",
    "https://www.edueco.in",
]

# Merge with settings if available
try:
    if settings.BACKEND_CORS_ORIGINS:
        for origin in settings.BACKEND_CORS_ORIGINS:
            if origin not in all_cors_origins:
                all_cors_origins.append(origin)
except NameError:
    pass

# Remove any wildcards if we want to allow credentials
if "*" in all_cors_origins:
    all_cors_origins.remove("*")

logger.info(f"CORS origins configured: {all_cors_origins}")

# --- MIDDLEWARE STACK (Order is critical) ---

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 2. Correlation ID Middleware (For tracing)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    import time
    import uuid
    
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# Error Handler for Global Exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please try again later."},
    )

# Include Routers
app.include_router(api_router, prefix=API_V1_STR)

@app.get("/")
async def root():
    return {"message": "EduEcosystem Backend API is live", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
