"""Zone management endpoints."""

import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.database import User
from app.models.schemas import ZoneCreate, ZoneResponse
from app.db import crud

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/cameras/{camera_id}/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    camera_id: str = Path(..., description="Camera identifier"),
    zone_data: ZoneCreate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new zone for a camera.

    Args:
        camera_id: Camera identifier
        zone_data: Zone creation data
        current_user: Authenticated user
        db: Database session

    Returns:
        Created zone

    Raises:
        HTTPException: If camera not found or doesn't belong to user
    """
    try:
        # Get or create camera
        camera = await crud.get_camera(db, camera_id)
        if not camera:
            # Auto-create camera if it doesn't exist
            camera = await crud.create_camera(
                db=db,
                camera_id=camera_id,
                name=f"Camera {camera_id}",
                user_id=current_user.id,
            )
            logger.info(f"Auto-created camera: {camera_id} for user {current_user.email}")
        elif camera.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this camera",
            )

        # Validate coordinates (must have at least 3 points for a polygon)
        if len(zone_data.coordinates) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zone must have at least 3 coordinate points",
            )

        # Create zone
        zone = await crud.create_zone(
            db=db,
            camera_id=camera_id,
            name=zone_data.name,
            coordinates=zone_data.coordinates,
            alert_type=zone_data.alert_type,
            active=zone_data.active,
            active_hours=zone_data.active_hours,
        )

        logger.info(f"Created zone {zone.name} for camera {camera_id}")

        # Convert to response format
        zone_response = ZoneResponse(
            id=zone.id,
            camera_id=zone.camera_id,
            name=zone.name,
            coordinates=json.loads(zone.coordinates_json),
            alert_type=zone.alert_type,
            active=zone.active,
            active_hours=zone.active_hours,
            created_at=zone.created_at,
        )

        return zone_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating zone: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating zone: {str(e)}",
        )


@router.get("/cameras/{camera_id}/zones", response_model=List[ZoneResponse])
async def get_zones(
    camera_id: str = Path(..., description="Camera identifier"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all zones for a camera.

    Args:
        camera_id: Camera identifier
        current_user: Authenticated user
        db: Database session

    Returns:
        List of zones

    Raises:
        HTTPException: If camera not found or doesn't belong to user
    """
    try:
        # Get or create camera
        camera = await crud.get_camera(db, camera_id)
        if not camera:
            # Auto-create camera if it doesn't exist
            camera = await crud.create_camera(
                db=db,
                camera_id=camera_id,
                name=f"Camera {camera_id}",
                user_id=current_user.id,
            )
            logger.info(f"Auto-created camera: {camera_id} for user {current_user.email}")
        elif camera.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this camera's zones",
            )

        # Get all zones (including inactive)
        zones = await crud.get_camera_zones(db, camera_id, active_only=False)

        # Convert to response format
        zone_responses = [
            ZoneResponse(
                id=zone.id,
                camera_id=zone.camera_id,
                name=zone.name,
                coordinates=json.loads(zone.coordinates_json),
                alert_type=zone.alert_type,
                active=zone.active,
                active_hours=zone.active_hours,
                created_at=zone.created_at,
            )
            for zone in zones
        ]

        return zone_responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting zones: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving zones: {str(e)}",
        )


@router.delete("/cameras/{camera_id}/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    camera_id: str = Path(..., description="Camera identifier"),
    zone_id: int = Path(..., description="Zone identifier"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a zone.

    Args:
        camera_id: Camera identifier
        zone_id: Zone identifier
        current_user: Authenticated user
        db: Database session

    Raises:
        HTTPException: If zone not found or doesn't belong to user
    """
    try:
        # Get zone
        zone = await crud.get_zone(db, zone_id)
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Zone {zone_id} not found",
            )

        # Verify zone belongs to the specified camera
        if zone.camera_id != camera_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Zone {zone_id} does not belong to camera {camera_id}",
            )

        # Check if camera belongs to user
        camera = await crud.get_camera(db, zone.camera_id)
        if not camera or camera.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this zone",
            )

        # Delete zone
        await crud.delete_zone(db, zone_id)
        logger.info(f"Deleted zone {zone_id} for camera {camera_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting zone: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting zone: {str(e)}",
        )
