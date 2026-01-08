"""Tests for detection endpoint."""

import pytest
from httpx import AsyncClient
from PIL import Image
import io

from app.main import app
from app.services.yolo_service import yolo_service


def create_test_image() -> bytes:
    """Create a simple test image."""
    img = Image.new("RGB", (640, 480), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


@pytest.mark.asyncio
async def test_detect_endpoint_no_auth():
    """Test detection endpoint without authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create test image
        image_data = create_test_image()

        response = await client.post(
            "/api/v1/detect",
            files={"image": ("test.jpg", image_data, "image/jpeg")},
            data={"camera_id": "test_cam"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_detect_endpoint_invalid_auth():
    """Test detection endpoint with invalid authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create test image
        image_data = create_test_image()

        response = await client.post(
            "/api/v1/detect",
            headers={"Authorization": "Bearer invalid_key"},
            files={"image": ("test.jpg", image_data, "image/jpeg")},
            data={"camera_id": "test_cam"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "model_loaded" in data
    assert "database_connected" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "CivicSentinel API"
    assert "version" in data
    assert data["status"] == "running"
