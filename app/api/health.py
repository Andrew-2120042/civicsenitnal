"""Health check endpoint."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.database import get_db
from app.models.schemas import HealthResponse
from app.services.yolo_service import yolo_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.

    Args:
        db: Database session

    Returns:
        Health status including model and database status
    """
    # Check if YOLO model is loaded
    model_loaded = yolo_service.model_loaded

    # Check database connection
    database_connected = False
    try:
        # Try a simple query
        await db.execute(text("SELECT 1"))
        database_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    # Determine overall status
    if model_loaded and database_connected:
        status = "healthy"
    elif not model_loaded and not database_connected:
        status = "unhealthy"
    else:
        status = "degraded"

    return HealthResponse(
        status=status,
        model_loaded=model_loaded,
        database_connected=database_connected,
        timestamp=datetime.utcnow(),
    )
