"""Detection endpoint for processing camera frames."""

import json
import logging
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image
import io

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.database import User
from app.models.schemas import DetectionResponse
from app.services.yolo_service import yolo_service
from app.services.zone_service import zone_service
from app.services.auth_service import auth_service
from app.db import crud

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/detect", response_model=DetectionResponse)
async def detect_objects(
    image: Annotated[UploadFile, File(description="Image file to process")],
    camera_id: Annotated[str, Form(description="Camera identifier")],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Process camera frame and detect persons in restricted zones.

    Args:
        image: Uploaded image file
        camera_id: Camera identifier
        current_user: Authenticated user
        db: Database session

    Returns:
        DetectionResponse with detections and alerts

    Raises:
        HTTPException: If camera limit exceeded or processing fails
    """
    try:
        # Check camera limit
        allowed, message = await auth_service.check_camera_limit(db, current_user, camera_id)
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

        # Get or create camera
        camera = await crud.get_camera(db, camera_id)
        if not camera:
            # Create new camera
            camera = await crud.create_camera(
                db=db,
                camera_id=camera_id,
                name=f"Camera {camera_id}",
                user_id=current_user.id,
            )
            logger.info(f"Created new camera: {camera_id} for user {current_user.email}")

        # Update last frame timestamp
        await crud.update_camera_last_frame(db, camera_id)

        # Read and validate image
        try:
            image_data = await image.read()
            pil_image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

        except Exception as e:
            logger.error(f"Failed to read image: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image file: {str(e)}",
            )

        # Run YOLO detection
        detections = yolo_service.detect_objects(pil_image)
        logger.info(f"Detected {len(detections)} persons in frame from camera {camera_id}")

        # Get active zones for this camera
        zones = await crud.get_camera_zones(db, camera_id, active_only=True)

        # Check for zone violations
        alerts = zone_service.check_zones(detections, zones)

        # Save alerts to database
        for alert in alerts:
            # Find the corresponding zone
            zone = next((z for z in zones if z.id == alert.zone_id), None)
            if zone:
                await crud.create_alert(
                    db=db,
                    camera_id=camera_id,
                    zone_id=zone.id,
                    detection_type="person",
                    confidence=alert.confidence,
                    bbox_json=None,  # Could add bbox data here if needed
                    image_url=None,  # Could add S3 URL here in future
                )
                logger.info(f"Created alert for zone {zone.name}")

        # Prepare response
        response = DetectionResponse(
            camera_id=camera_id,
            timestamp=datetime.utcnow(),
            detections=detections,
            alerts=alerts,
        )

        # Debug logging
        logger.info(f"Returning response with {len(detections)} detections and {len(alerts)} alerts")
        if alerts:
            logger.info(f"Alert details: {[{'zone_name': a.zone_name, 'confidence': a.confidence} for a in alerts]}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing detection: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing frame: {str(e)}",
        )
