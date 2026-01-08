"""Test script for CivicSentinel API."""

import asyncio
import requests
from pathlib import Path
from PIL import Image, ImageDraw
import io

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "test_api_key_123"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def create_test_image():
    """Create a simple test image with a rectangle (simulating a person)."""
    # Create a 640x480 image
    img = Image.new("RGB", (640, 480), color="white")
    draw = ImageDraw.Draw(img)

    # Draw a rectangle (simulating a person) in the center
    # Person will be at coordinates roughly (270, 140) to (370, 340)
    draw.rectangle([(270, 140), (370, 340)], fill="blue", outline="black", width=2)

    # Save image
    test_image_path = Path("test_images/sample_test.jpg")
    test_image_path.parent.mkdir(exist_ok=True)
    img.save(test_image_path)
    print(f"✓ Created test image: {test_image_path}")

    return test_image_path


def test_health_check():
    """Test health check endpoint."""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Health check passed")
        print(f"  Status: {data['status']}")
        print(f"  Model loaded: {data['model_loaded']}")
        print(f"  Database connected: {data['database_connected']}")
        return True
    else:
        print(f"✗ Health check failed: {response.status_code}")
        print(f"  {response.text}")
        return False


def test_create_zone(camera_id: str):
    """Test creating a zone."""
    print("\n=== Testing Zone Creation ===")

    # Define a zone in the center of the image where our test "person" is
    zone_data = {
        "name": "Restricted Area - Center",
        "coordinates": [
            [200, 100],  # Top-left
            [440, 100],  # Top-right
            [440, 380],  # Bottom-right
            [200, 380],  # Bottom-left
        ],
        "alert_type": "intrusion",
        "active": True,
    }

    response = requests.post(
        f"{BASE_URL}/cameras/{camera_id}/zones", headers=HEADERS, json=zone_data
    )

    if response.status_code == 201:
        data = response.json()
        print(f"✓ Zone created successfully")
        print(f"  Zone ID: {data['id']}")
        print(f"  Zone Name: {data['name']}")
        print(f"  Coordinates: {data['coordinates']}")
        return data["id"]
    else:
        print(f"✗ Zone creation failed: {response.status_code}")
        print(f"  {response.text}")
        return None


def test_get_zones(camera_id: str):
    """Test getting zones for a camera."""
    print("\n=== Testing Get Zones ===")

    response = requests.get(f"{BASE_URL}/cameras/{camera_id}/zones", headers=HEADERS)

    if response.status_code == 200:
        zones = response.json()
        print(f"✓ Retrieved {len(zones)} zone(s)")
        for zone in zones:
            print(f"  - {zone['name']} (ID: {zone['id']})")
        return True
    else:
        print(f"✗ Get zones failed: {response.status_code}")
        print(f"  {response.text}")
        return False


def test_detection(image_path: Path, camera_id: str):
    """Test detection endpoint."""
    print("\n=== Testing Detection ===")

    with open(image_path, "rb") as f:
        files = {"image": ("test.jpg", f, "image/jpeg")}
        data = {"camera_id": camera_id}

        response = requests.post(
            f"{BASE_URL}/detect", headers=HEADERS, files=files, data=data
        )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Detection successful")
        print(f"  Camera ID: {result['camera_id']}")
        print(f"  Timestamp: {result['timestamp']}")
        print(f"  Detections: {len(result['detections'])}")

        for i, detection in enumerate(result["detections"], 1):
            print(
                f"    {i}. {detection['class']} - "
                f"Confidence: {detection['confidence']:.2f}"
            )

        print(f"  Alerts: {len(result['alerts'])}")
        for i, alert in enumerate(result["alerts"], 1):
            print(
                f"    {i}. Zone: {alert['zone_name']} - "
                f"Type: {alert['alert_type']} - "
                f"Confidence: {alert['confidence']:.2f}"
            )

        return True
    else:
        print(f"✗ Detection failed: {response.status_code}")
        print(f"  {response.text}")
        return False


def test_get_alerts(camera_id: str):
    """Test getting alerts."""
    print("\n=== Testing Get Alerts ===")

    params = {"camera_id": camera_id, "page": 1, "page_size": 10}
    response = requests.get(f"{BASE_URL}/alerts", headers=HEADERS, params=params)

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved alerts")
        print(f"  Total alerts: {data['total']}")
        print(f"  Page: {data['page']}")
        print(f"  Alerts on this page: {len(data['alerts'])}")

        for alert in data["alerts"]:
            print(
                f"    - {alert['detection_type']} in zone {alert['zone_id']} "
                f"(confidence: {alert['confidence']:.2f})"
            )
        return True
    else:
        print(f"✗ Get alerts failed: {response.status_code}")
        print(f"  {response.text}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("CivicSentinel API Test Suite")
    print("=" * 60)

    camera_id = "test_camera_001"

    # Create test image
    test_image_path = create_test_image()

    # Test 1: Health check
    if not test_health_check():
        print("\n⚠ Health check failed. Make sure the API is running.")
        print("  Run: poetry run uvicorn app.main:app --reload")
        return

    # Test 2: Create a zone
    zone_id = test_create_zone(camera_id)
    if not zone_id:
        print("\n⚠ Zone creation failed. Some tests may not work correctly.")

    # Test 3: Get zones
    test_get_zones(camera_id)

    # Test 4: Run detection (should trigger alert if person detected in zone)
    test_detection(test_image_path, camera_id)

    # Test 5: Get alerts
    test_get_alerts(camera_id)

    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
