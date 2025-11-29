# YOLO Object Detection Demo

A comprehensive standalone demo suite to visualize how YOLO object detection works with bounding boxes and zone-based intrusion detection.

## Demo Versions

### 1. Basic Detection Demo
Simple video detection with bounding boxes - great for understanding the basics.

### 2. Zone-Based Detection Demo (FULL FEATURED)
**Interactive demo with zone drawing and intrusion alerts** - shows the complete detection workflow:
- Draw custom detection zones on video
- Real-time intrusion detection when objects enter zones
- Visual alerts and zone highlighting
- Save/load zone configurations

## What This Shows You

This demo suite demonstrates:
- **Real-time object detection** on video files
- **Bounding boxes** drawn around detected objects
- **Zone-based intrusion detection** with custom areas
- **Visual alerts** when intrusions occur
- **Confidence scores** for each detection
- **Object labels** (person, car, truck, etc.)
- **Detection statistics** and tracking

## Requirements

- Python 3.8+
- OpenCV (cv2)
- Ultralytics YOLO
- NumPy

## Installation

```bash
# Install required packages
pip install opencv-python ultralytics numpy
```

## Quick Start

### Zone-Based Demo (Recommended)

Run the **full-featured zone-based detection demo**:

```bash
./run_zone_demo.sh
```

Or manually:
```bash
python3 detect_with_zones.py test-people.mp4
```

See **[ZONE_DEMO_GUIDE.md](ZONE_DEMO_GUIDE.md)** for complete instructions.

### Basic Detection Demo

Run simple detection on a video file:

```bash
python detect_video.py path/to/your/video.mp4
```

### Save Output Video

Save the processed video with bounding boxes:

```bash
python detect_video.py input.mp4 --output output.mp4
```

### Adjust Confidence Threshold

Only show detections above a certain confidence level (0-1):

```bash
python detect_video.py video.mp4 --confidence 0.7
```

### Use Different Model

Use a different YOLO model:

```bash
python detect_video.py video.mp4 --model path/to/model.pt
```

## Example with Sample Video

```bash
# Copy a video to test
cp ../civicsentinel-agent/test-videos/*.mp4 ./sample.mp4

# Run detection
python detect_video.py sample.mp4

# Or save the output
python detect_video.py sample.mp4 --output detected.mp4
```

## Controls During Playback

- **Q** - Quit the demo
- **P** - Pause/Resume playback
- **S** - Save current frame as image

## What You'll See

The video will play with:
- **Green boxes** around detected persons
- **Blue boxes** around detected cars
- **Orange boxes** around detected trucks
- **Yellow boxes** around other detected objects

Each box shows:
- Object class name (e.g., "person", "car")
- Confidence score (e.g., "0.85")

Top left corner shows:
- Current frame number
- Total detections in current frame

## Understanding the Output

At the end, you'll see statistics like:

```
==================================================
Detection Statistics:
==================================================
person: 156 detections
car: 23 detections
truck: 5 detections
==================================================
```

This shows how many times each object was detected across all frames.

## Features

1. **Color-coded detections**: Different colors for different object types
2. **Confidence filtering**: Only show high-confidence detections
3. **Frame-by-frame processing**: See detection on every frame
4. **Export capability**: Save processed video with annotations
5. **Real-time statistics**: See detection counts as video plays

## Troubleshooting

**"Could not open video"**
- Make sure the video file path is correct
- Supported formats: .mp4, .avi, .mov, .mkv

**"Model not found"**
- The default model path is `../yolov8s.pt`
- Make sure the YOLO model exists or specify a different path with `--model`

**Video plays too fast/slow**
- The playback speed matches the original video FPS
- Press 'P' to pause and examine detections closely

## How It Works

1. **Loads YOLO model** - Uses YOLOv8 for object detection
2. **Opens video file** - Reads video frame by frame
3. **Runs detection** - YOLO analyzes each frame for objects
4. **Draws boxes** - Adds bounding boxes and labels
5. **Displays result** - Shows the annotated video in real-time
6. **Saves statistics** - Counts all detections by type

## Use Cases

- **Learning**: Understand how object detection works visually
- **Testing**: Test YOLO model performance on your videos
- **Debugging**: Verify detection quality and confidence thresholds
- **Demonstration**: Show others how AI object detection works

## Files in This Demo

### Main Demo Scripts
- **`detect_with_zones.py`** - Full-featured zone-based detection with intrusion alerts
- **`detect_video.py`** - Basic detection with bounding boxes (GUI version)
- **`detect_video_nogui.py`** - No-GUI version for remote/headless execution

### Helper Scripts
- **`run_zone_demo.sh`** - One-click launcher for zone demo
- **`run_demo.sh`** - One-click launcher for basic demo

### Documentation
- **`ZONE_DEMO_GUIDE.md`** - Complete guide for zone-based detection
- **`QUICKSTART.md`** - Quick reference for basic demo
- **`README.md`** - This file

### Sample Files
- **`test-people.mp4`** - Sample video with people for testing
- **`zones_config.json`** - Saved zone configurations (created when you save zones)

## Notes

- This is a **demonstration tool**, not part of the main CivicSentinel project
- It processes videos **locally** on your machine
- No API calls or cloud processing
- Perfect for understanding detection before using it in production
- The **zone-based demo** shows the complete workflow you'd use in a real surveillance system
