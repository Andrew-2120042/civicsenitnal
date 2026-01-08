"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# Detection Schemas
class BoundingBox(BaseModel):
    """Bounding box coordinates."""

    x1: float = Field(..., description="Top-left x coordinate")
    y1: float = Field(..., description="Top-left y coordinate")
    x2: float = Field(..., description="Bottom-right x coordinate")
    y2: float = Field(..., description="Bottom-right y coordinate")


class Detection(BaseModel):
    """Single detection result."""

    class_name: str = Field(..., alias="class", description="Detected object class")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bbox: BoundingBox = Field(..., description="Bounding box coordinates")

    model_config = ConfigDict(populate_by_name=True)


class ZoneAlert(BaseModel):
    """Alert for zone intrusion."""

    zone_id: int = Field(..., description="Zone identifier")
    zone_name: str = Field(..., description="Zone name")
    alert_type: str = Field(..., description="Type of alert")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")


class DetectionResponse(BaseModel):
    """Response for detection endpoint."""

    camera_id: str = Field(..., description="Camera identifier")
    timestamp: datetime = Field(..., description="Detection timestamp")
    detections: List[Detection] = Field(default_factory=list, description="List of detections")
    alerts: List[ZoneAlert] = Field(default_factory=list, description="List of zone alerts")


# Zone Schemas
class ZoneCreate(BaseModel):
    """Schema for creating a new zone."""

    name: str = Field(..., min_length=1, max_length=255, description="Zone name")
    coordinates: List[List[float]] = Field(
        ...,
        min_length=3,
        description="Polygon coordinates as list of [x, y] points",
    )
    alert_type: str = Field(default="intrusion", description="Type of alert to generate")
    active: bool = Field(default=True, description="Whether zone is active")
    active_hours: Optional[str] = Field(None, description="Active hours in JSON format")


class ZoneResponse(BaseModel):
    """Response schema for zone."""

    id: int
    camera_id: str
    name: str
    coordinates: List[List[float]]
    alert_type: str
    active: bool
    active_hours: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Alert Schemas
class AlertResponse(BaseModel):
    """Response schema for alert."""

    id: int
    camera_id: str
    zone_id: int
    detection_type: str
    confidence: float
    bbox: Optional[BoundingBox] = None
    image_url: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertListResponse(BaseModel):
    """Paginated alert list response."""

    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int


# Health Check Schema
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Overall health status")
    model_loaded: bool = Field(..., description="Whether YOLO model is loaded")
    database_connected: bool = Field(..., description="Whether database is accessible")
    timestamp: datetime = Field(..., description="Health check timestamp")


# Camera Schemas
class CameraResponse(BaseModel):
    """Response schema for camera."""

    id: str
    name: str
    location: Optional[str] = None
    active: bool
    created_at: datetime
    last_frame_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# User Schemas
class UserResponse(BaseModel):
    """Response schema for user."""

    id: int
    email: str
    plan: str
    cameras_allowed: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
