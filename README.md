# CivicSentinel API

AI-powered CCTV surveillance system for detecting persons in restricted zones using YOLOv8 and FastAPI.

## Features

- **Person Detection**: Real-time person detection using YOLOv8s
- **Zone Monitoring**: Define restricted zones and get alerts when persons enter
- **REST API**: Clean RESTful API for easy integration
- **Authentication**: API key-based authentication with user limits
- **Database**: SQLite for easy setup (PostgreSQL-ready)
- **Docker Support**: Containerized deployment

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Desktop Agent  │────>│  CivicSentinel  │────>│ YOLO Model   │
│  (Camera Feed)  │     │      API        │     │  Detection   │
└─────────────────┘     └─────────────────┘     └──────────────┘
                               │
                               ├──> Zone Check
                               ├──> Alert Generation
                               └──> Database Storage
```

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**:
   ```bash
   cd civicsentinel
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

4. **Initialize database**:
   ```bash
   poetry run python init_db.py
   ```

5. **Run the server**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

6. **Access API documentation**:
   Open http://localhost:8000/docs in your browser

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Documentation

### Authentication

All endpoints (except `/health`) require authentication via API key in the Authorization header:

```
Authorization: Bearer <your_api_key>
```

**Test API Key**: `test_api_key_123`

### Endpoints

#### 1. Health Check

**GET** `/api/v1/health`

Check API health status.

**Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "database_connected": true,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### 2. Detect Objects

**POST** `/api/v1/detect`

Process camera frame and detect persons in zones.

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `image`: Image file (JPEG, PNG)
  - `camera_id`: Camera identifier (string)

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/detect \
  -H "Authorization: Bearer test_api_key_123" \
  -F "image=@test_images/sample_test.jpg" \
  -F "camera_id=cam_001"
```

**Response**:
```json
{
  "camera_id": "cam_001",
  "timestamp": "2025-01-15T10:30:00Z",
  "detections": [
    {
      "class": "person",
      "confidence": 0.87,
      "bbox": {
        "x1": 100,
        "y1": 200,
        "x2": 300,
        "y2": 400
      }
    }
  ],
  "alerts": [
    {
      "zone_id": 1,
      "zone_name": "Restricted Area",
      "alert_type": "intrusion",
      "confidence": 0.87
    }
  ]
}
```

#### 3. Create Zone

**POST** `/api/v1/cameras/{camera_id}/zones`

Create a restricted zone for a camera.

**Request Body**:
```json
{
  "name": "Restricted Area",
  "coordinates": [
    [100, 200],
    [400, 200],
    [400, 500],
    [100, 500]
  ],
  "alert_type": "intrusion",
  "active": true
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/cameras/cam_001/zones \
  -H "Authorization: Bearer test_api_key_123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Restricted Area",
    "coordinates": [[100, 200], [400, 200], [400, 500], [100, 500]],
    "alert_type": "intrusion"
  }'
```

**Response**:
```json
{
  "id": 1,
  "camera_id": "cam_001",
  "name": "Restricted Area",
  "coordinates": [[100, 200], [400, 200], [400, 500], [100, 500]],
  "alert_type": "intrusion",
  "active": true,
  "active_hours": null,
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### 4. Get Zones

**GET** `/api/v1/cameras/{camera_id}/zones`

Get all zones for a camera.

**Example**:
```bash
curl -X GET http://localhost:8000/api/v1/cameras/cam_001/zones \
  -H "Authorization: Bearer test_api_key_123"
```

#### 5. Delete Zone

**DELETE** `/api/v1/zones/{zone_id}`

Delete a zone.

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/zones/1 \
  -H "Authorization: Bearer test_api_key_123"
```

#### 6. Get Alerts

**GET** `/api/v1/alerts`

Get alert history with optional filters.

**Query Parameters**:
- `camera_id` (optional): Filter by camera
- `start_date` (optional): Filter by start date
- `end_date` (optional): Filter by end date
- `alert_type` (optional): Filter by alert type
- `page` (default: 1): Page number
- `page_size` (default: 50): Items per page

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/alerts?camera_id=cam_001&page=1&page_size=10" \
  -H "Authorization: Bearer test_api_key_123"
```

**Response**:
```json
{
  "alerts": [
    {
      "id": 1,
      "camera_id": "cam_001",
      "zone_id": 1,
      "detection_type": "person",
      "confidence": 0.87,
      "bbox": null,
      "image_url": null,
      "timestamp": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

## Testing

### Run Test Script

```bash
# Make sure the API is running first
poetry run uvicorn app.main:app --reload

# In another terminal, run the test script
poetry run python test_api.py
```

### Run Unit Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_zones.py -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection URL | `sqlite+aiosqlite:///./civicsentinel.db` |
| `MODEL_PATH` | Path to YOLO model | `models/yolov8s.pt` |
| `MODEL_CONFIDENCE_THRESHOLD` | Detection confidence threshold | `0.5` |
| `MODEL_FRAME_SIZE` | Frame processing size | `640` |
| `MAX_CAMERAS_FREE_PLAN` | Camera limit for free plan | `2` |
| `MAX_CAMERAS_PRO_PLAN` | Camera limit for pro plan | `10` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `TEST_API_KEY` | Test API key (dev only) | `test_api_key_123` |

## Project Structure

```
civicsentinel/
├── app/
│   ├── api/                  # API endpoints
│   │   ├── detect.py        # Detection endpoint
│   │   ├── zones.py         # Zone management
│   │   ├── alerts.py        # Alert history
│   │   └── health.py        # Health check
│   ├── db/                   # Database layer
│   │   ├── database.py      # DB connection
│   │   └── crud.py          # CRUD operations
│   ├── models/               # Data models
│   │   ├── database.py      # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/             # Business logic
│   │   ├── yolo_service.py  # YOLO detection
│   │   ├── zone_service.py  # Zone checking
│   │   └── auth_service.py  # Authentication
│   ├── config.py             # Configuration
│   ├── dependencies.py       # FastAPI dependencies
│   └── main.py               # Application entry
├── tests/                    # Unit tests
├── models/                   # YOLO model weights
├── test_images/              # Test images
├── pyproject.toml            # Poetry configuration
├── Dockerfile                # Docker image
├── docker-compose.yml        # Docker compose config
├── init_db.py                # Database initialization
├── test_api.py               # API test script
└── README.md                 # This file
```

## How It Works

### Detection Flow

1. **Image Upload**: Desktop agent uploads camera frame via `/api/v1/detect` endpoint
2. **YOLO Processing**: Frame is processed by YOLOv8s model to detect persons
3. **Zone Checking**: Each detected person's bounding box center is checked against active zones
4. **Alert Generation**: If person is in restricted zone, alert is created
5. **Response**: API returns detections and alerts to client

### Zone Detection Algorithm

1. **Polygon Definition**: Zones are defined as polygons (minimum 3 points)
2. **Center Calculation**: Bounding box center is calculated: `(x1+x2)/2, (y1+y2)/2`
3. **Point-in-Polygon**: Uses Shapely library to check if center point is inside polygon
4. **Alert Creation**: If point is inside, alert is generated and stored

## Performance

- **Processing Speed**: ~200-500ms per frame (depends on image size)
- **Throughput**: Supports 5-10 FPS per camera
- **Model Size**: YOLOv8s (~22MB)
- **Memory**: ~500MB RAM with model loaded

## Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Image storage (S3/MinIO integration)
- [ ] PostgreSQL support for production
- [ ] Multiple detection classes (vehicles, etc.)
- [ ] Loitering detection (time-based alerts)
- [ ] Dashboard UI
- [ ] Email/SMS notifications
- [ ] Video stream support

## Troubleshooting

### Model Download Issues

If YOLO model fails to download:

```bash
# Manually download model
poetry run python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"
```

### Database Issues

If database initialization fails:

```bash
# Remove and recreate database
rm civicsentinel.db
poetry run python init_db.py
```

### Port Already in Use

If port 8000 is already in use:

```bash
# Run on different port
poetry run uvicorn app.main:app --port 8001
```

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/civicsentinel/issues
- Email: support@civicsentinel.com

---

**Built with**: FastAPI, YOLOv8, SQLAlchemy, Shapely, and ❤️
