# Getting Started with CivicSentinel

Quick guide to get CivicSentinel up and running in 5 minutes.

## Prerequisites

- **Python 3.11 or higher**: Check with `python3 --version`
- **Poetry**: Install from https://python-poetry.org/docs/#installation

## Option 1: Quick Start (Recommended)

Run the quick start script:

```bash
./quickstart.sh
```

This will:
1. Install all dependencies
2. Create `.env` file
3. Initialize the database with a test user

Then start the server:

```bash
poetry run uvicorn app.main:app --reload
```

## Option 2: Manual Setup

### Step 1: Install Dependencies

```bash
poetry install
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` if needed (default values work fine for development).

### Step 3: Initialize Database

```bash
poetry run python init_db.py
```

This creates:
- SQLite database (`civicsentinel.db`)
- Test user with email: `test@civicsentinel.com`
- Test API key: `test_api_key_123`

### Step 4: Start the Server

```bash
poetry run uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## Verify Installation

### 1. Check Health Endpoint

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "database_connected": true,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### 2. View API Documentation

Open in your browser:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Run Test Script

In a new terminal:

```bash
poetry run python test_api.py
```

This will:
1. Create a test image
2. Create a zone
3. Run detection
4. Generate alerts
5. Retrieve alert history

## Your First Detection

### 1. Create a Test Zone

```bash
curl -X POST http://localhost:8000/api/v1/cameras/my_camera/zones \
  -H "Authorization: Bearer test_api_key_123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Restricted Area",
    "coordinates": [[100, 100], [500, 100], [500, 400], [100, 400]],
    "alert_type": "intrusion"
  }'
```

### 2. Upload an Image for Detection

```bash
curl -X POST http://localhost:8000/api/v1/detect \
  -H "Authorization: Bearer test_api_key_123" \
  -F "image=@test_images/sample_test.jpg" \
  -F "camera_id=my_camera"
```

### 3. View Alerts

```bash
curl -X GET http://localhost:8000/api/v1/alerts?camera_id=my_camera \
  -H "Authorization: Bearer test_api_key_123"
```

## Docker Deployment

If you prefer Docker:

```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Troubleshooting

### "Model not loaded"

The YOLO model downloads automatically on first run. This may take a minute.

Wait and refresh, or manually download:
```bash
poetry run python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"
```

### "Port already in use"

Change the port in `.env`:
```bash
API_PORT=8001
```

Or run with custom port:
```bash
poetry run uvicorn app.main:app --port 8001
```

### Database errors

Remove and recreate:
```bash
rm civicsentinel.db
poetry run python init_db.py
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API at http://localhost:8000/docs
- Check out the [test_api.py](test_api.py) script for usage examples
- Run tests: `poetry run pytest`

## Support

Having issues? Check:
- Python version is 3.11+
- Poetry is installed correctly
- All dependencies installed: `poetry install`
- Database initialized: `poetry run python init_db.py`

---

Happy detecting! 🎥🔍
