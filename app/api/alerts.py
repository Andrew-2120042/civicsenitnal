"""Alerts endpoint for retrieving alert history."""

import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.database import User
from app.models.schemas import AlertResponse, AlertListResponse, BoundingBox
from app.db import crud

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/alerts", response_model=AlertListResponse)
async def get_alerts(
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get alert history with optional filters.

    Args:
        camera_id: Optional camera ID filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        alert_type: Optional alert type filter
        page: Page number (1-indexed)
        page_size: Number of items per page
        current_user: Authenticated user
        db: Database session

    Returns:
        Paginated list of alerts

    Raises:
        HTTPException: If camera doesn't belong to user
    """
    try:
        # If camera_id is provided, verify it belongs to user
        if camera_id:
            camera = await crud.get_camera(db, camera_id)
            if not camera:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Camera {camera_id} not found",
                )
            if camera.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this camera's alerts",
                )
        else:
            # If no camera_id, get all user's cameras
            user_cameras = await crud.get_user_cameras(db, current_user.id)
            camera_ids = [cam.id for cam in user_cameras]

        # Calculate offset
        offset = (page - 1) * page_size

        # Get alerts
        alerts, total = await crud.get_alerts(
            db=db,
            camera_id=camera_id,
            start_date=start_date,
            end_date=end_date,
            alert_type=alert_type,
            limit=page_size,
            offset=offset,
        )

        # If no camera_id was specified, filter alerts to only user's cameras
        if not camera_id:
            alerts = [alert for alert in alerts if alert.camera_id in camera_ids]
            total = len(alerts)

        # Convert to response format
        alert_responses = []
        for alert in alerts:
            bbox = None
            if alert.bbox_json:
                try:
                    bbox_data = json.loads(alert.bbox_json)
                    bbox = BoundingBox(**bbox_data)
                except Exception as e:
                    logger.warning(f"Failed to parse bbox for alert {alert.id}: {e}")

            alert_responses.append(
                AlertResponse(
                    id=alert.id,
                    camera_id=alert.camera_id,
                    zone_id=alert.zone_id,
                    detection_type=alert.detection_type,
                    confidence=alert.confidence,
                    bbox=bbox,
                    image_url=alert.image_url,
                    timestamp=alert.timestamp,
                )
            )

        return AlertListResponse(
            alerts=alert_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving alerts: {str(e)}",
        )
