"""CRUD operations for database models."""

import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import User, Camera, Zone, Alert


# User CRUD
async def get_user_by_api_key(db: AsyncSession, api_key: str) -> Optional[User]:
    """Get user by API key."""
    result = await db.execute(select(User).where(User.api_key == api_key))
    return result.scalars().first()


async def create_user(
    db: AsyncSession, email: str, api_key: str, plan: str = "free", cameras_allowed: int = 2
) -> User:
    """Create a new user."""
    user = User(
        email=email,
        api_key=api_key,
        plan=plan,
        cameras_allowed=cameras_allowed,
        status="active",
    )
    db.add(user)
    await db.flush()
    return user


# Camera CRUD
async def get_camera(db: AsyncSession, camera_id: str) -> Optional[Camera]:
    """Get camera by ID."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    return result.scalars().first()


async def get_user_cameras(db: AsyncSession, user_id: int) -> List[Camera]:
    """Get all cameras for a user."""
    result = await db.execute(select(Camera).where(Camera.user_id == user_id))
    return list(result.scalars().all())


async def create_camera(
    db: AsyncSession, camera_id: str, name: str, user_id: int, location: Optional[str] = None
) -> Camera:
    """Create a new camera."""
    camera = Camera(
        id=camera_id,
        name=name,
        user_id=user_id,
        location=location,
        active=True,
    )
    db.add(camera)
    await db.flush()
    return camera


async def update_camera_last_frame(db: AsyncSession, camera_id: str) -> None:
    """Update camera's last frame timestamp."""
    camera = await get_camera(db, camera_id)
    if camera:
        camera.last_frame_at = datetime.utcnow()
        await db.flush()


# Zone CRUD
async def get_zone(db: AsyncSession, zone_id: int) -> Optional[Zone]:
    """Get zone by ID."""
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    return result.scalars().first()


async def get_camera_zones(db: AsyncSession, camera_id: str, active_only: bool = True) -> List[Zone]:
    """Get all zones for a camera."""
    query = select(Zone).where(Zone.camera_id == camera_id)
    if active_only:
        query = query.where(Zone.active == True)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_zone(
    db: AsyncSession,
    camera_id: str,
    name: str,
    coordinates: List[List[float]],
    alert_type: str = "intrusion",
    active: bool = True,
    active_hours: Optional[str] = None,
) -> Zone:
    """Create a new zone."""
    zone = Zone(
        camera_id=camera_id,
        name=name,
        coordinates_json=json.dumps(coordinates),
        alert_type=alert_type,
        active=active,
        active_hours=active_hours,
    )
    db.add(zone)
    await db.flush()
    return zone


async def delete_zone(db: AsyncSession, zone_id: int) -> bool:
    """Delete a zone and all related alerts."""
    zone = await get_zone(db, zone_id)
    if zone:
        # First delete all alerts related to this zone
        alerts_result = await db.execute(select(Alert).where(Alert.zone_id == zone_id))
        alerts = list(alerts_result.scalars().all())
        for alert in alerts:
            await db.delete(alert)

        # Then delete the zone
        await db.delete(zone)
        await db.flush()
        return True
    return False


# Alert CRUD
async def create_alert(
    db: AsyncSession,
    camera_id: str,
    zone_id: int,
    detection_type: str,
    confidence: float,
    bbox_json: Optional[str] = None,
    image_url: Optional[str] = None,
) -> Alert:
    """Create a new alert."""
    alert = Alert(
        camera_id=camera_id,
        zone_id=zone_id,
        detection_type=detection_type,
        confidence=confidence,
        bbox_json=bbox_json,
        image_url=image_url,
        timestamp=datetime.utcnow(),
    )
    db.add(alert)
    await db.flush()
    return alert


async def get_alerts(
    db: AsyncSession,
    camera_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    alert_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[List[Alert], int]:
    """Get alerts with optional filters."""
    # Build query
    query = select(Alert)
    conditions = []

    if camera_id:
        conditions.append(Alert.camera_id == camera_id)
    if start_date:
        conditions.append(Alert.timestamp >= start_date)
    if end_date:
        conditions.append(Alert.timestamp <= end_date)

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    count_query = select(Alert).where(and_(*conditions)) if conditions else select(Alert)
    total_result = await db.execute(count_query)
    total = len(list(total_result.scalars().all()))

    # Get paginated results
    query = query.order_by(desc(Alert.timestamp)).limit(limit).offset(offset)
    result = await db.execute(query)
    alerts = list(result.scalars().all())

    return alerts, total
