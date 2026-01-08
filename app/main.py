"""Main FastAPI application for CivicSentinel."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import init_db
from app.services.yolo_service import yolo_service
from app.api import detect, zones, alerts, health

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown.

    Handles:
    - Database initialization
    - YOLO model loading
    - Cleanup on shutdown
    """
    # Startup
    logger.info("Starting CivicSentinel API...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Load YOLO model
    try:
        yolo_service.load_model()
        logger.info("YOLO model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load YOLO model: {e}")

    logger.info("CivicSentinel API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down CivicSentinel API...")


# Create FastAPI app
app = FastAPI(
    title="CivicSentinel API",
    description="AI-powered CCTV surveillance system for detecting persons in restricted zones",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    detect.router,
    prefix="/api/v1",
    tags=["Detection"],
)

app.include_router(
    zones.router,
    prefix="/api/v1",
    tags=["Zones"],
)

app.include_router(
    alerts.router,
    prefix="/api/v1",
    tags=["Alerts"],
)

app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["Health"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "CivicSentinel API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
