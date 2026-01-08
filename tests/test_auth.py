"""Tests for authentication service."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.models.database import User, Camera
from app.services.auth_service import AuthService
from app.db import crud


@pytest.fixture
async def db_session():
    """Create a test database session."""
    # Create in-memory SQLite database for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = await crud.create_user(
        db=db_session,
        email="test@example.com",
        api_key="test_key_123",
        plan="free",
        cameras_allowed=2,
    )
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_verify_valid_api_key(db_session, test_user):
    """Test verifying a valid API key."""
    auth_service = AuthService()
    user = await auth_service.verify_api_key(db_session, "test_key_123")

    assert user is not None
    assert user.email == "test@example.com"
    assert user.status == "active"


@pytest.mark.asyncio
async def test_verify_invalid_api_key(db_session):
    """Test verifying an invalid API key."""
    auth_service = AuthService()
    user = await auth_service.verify_api_key(db_session, "invalid_key")

    assert user is None


@pytest.mark.asyncio
async def test_check_camera_limit_not_reached(db_session, test_user):
    """Test camera limit when not reached."""
    auth_service = AuthService()
    allowed, message = await auth_service.check_camera_limit(
        db_session, test_user, "camera_1"
    )

    assert allowed is True
    assert "limit not reached" in message.lower()


@pytest.mark.asyncio
async def test_check_camera_limit_reached(db_session, test_user):
    """Test camera limit when reached."""
    # Add 2 cameras (user's limit)
    await crud.create_camera(db_session, "cam_1", "Camera 1", test_user.id)
    await crud.create_camera(db_session, "cam_2", "Camera 2", test_user.id)
    await db_session.commit()

    auth_service = AuthService()
    allowed, message = await auth_service.check_camera_limit(
        db_session, test_user, "cam_3"
    )

    assert allowed is False
    assert "limit reached" in message.lower()


@pytest.mark.asyncio
async def test_check_existing_camera_allowed(db_session, test_user):
    """Test that existing camera is always allowed."""
    # Add a camera
    await crud.create_camera(db_session, "cam_1", "Camera 1", test_user.id)
    await db_session.commit()

    auth_service = AuthService()
    allowed, message = await auth_service.check_camera_limit(
        db_session, test_user, "cam_1"
    )

    assert allowed is True
    assert "already registered" in message.lower()
