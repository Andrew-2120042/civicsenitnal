"""SQLAlchemy database models."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    """User model for authentication and limits."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    api_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    plan: Mapped[str] = mapped_column(
        String(50), nullable=False, default="free"
    )  # free, pro, enterprise
    cameras_allowed: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )  # active, suspended, deleted
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    cameras: Mapped[List["Camera"]] = relationship("Camera", back_populates="user")


class Camera(Base):
    """Camera model for tracking registered cameras."""

    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_frame_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cameras")
    zones: Mapped[List["Zone"]] = relationship("Zone", back_populates="camera")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="camera")


class Zone(Base):
    """Zone model for restricted area definitions."""

    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    camera_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    coordinates_json: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # JSON array of [x, y] points
    alert_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="intrusion"
    )  # intrusion, loitering, etc.
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    active_hours: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )  # JSON for time restrictions
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    camera: Mapped["Camera"] = relationship("Camera", back_populates="zones")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="zone")


class Alert(Base):
    """Alert model for detection events."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    camera_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zone_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    detection_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="person"
    )  # person, vehicle, etc.
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON bbox coordinates
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    extra_data: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Additional data
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    camera: Mapped["Camera"] = relationship("Camera", back_populates="alerts")
    zone: Mapped["Zone"] = relationship("Zone", back_populates="alerts")
