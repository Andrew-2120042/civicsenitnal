#!/bin/bash

# YOLO Detection Demo Quick Start Script

echo "=========================================="
echo "   YOLO Detection Demo - Quick Start"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Check if required packages are installed
echo "Checking required packages..."
python3 -c "import cv2; import ultralytics; import numpy" 2>/dev/null

if [ $? -ne 0 ]; then
    echo ""
    echo "Some packages are missing. Installing..."
    pip install opencv-python ultralytics numpy
    echo ""
fi

echo "=========================================="
echo ""

# Check if sample video exists
if [ ! -f "sample-video.mp4" ]; then
    echo "Error: sample-video.mp4 not found"
    echo "Please add a video file named 'sample-video.mp4' to this directory"
    exit 1
fi

# Check if YOLO model exists
if [ ! -f "../yolov8s.pt" ]; then
    echo "Warning: YOLO model not found at ../yolov8s.pt"
    echo "The model will be downloaded automatically on first run"
    echo ""
fi

echo "Starting detection demo..."
echo ""
echo "Controls:"
echo "  Q - Quit"
echo "  P - Pause/Resume"
echo "  S - Save current frame"
echo ""
echo "=========================================="
echo ""

# Run the detection
python3 detect_video.py sample-video.mp4

echo ""
echo "=========================================="
echo "Demo completed!"
echo "=========================================="
