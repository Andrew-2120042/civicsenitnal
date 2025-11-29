#!/bin/bash

# Zone-Based Detection Demo Quick Start

echo "==========================================="
echo "  Zone-Based Detection Demo - Quick Start"
echo "==========================================="
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

echo "==========================================="
echo ""

# Check if sample video exists
if [ ! -f "test-people.mp4" ]; then
    echo "Error: test-people.mp4 not found"
    echo "Please run the basic demo first to download the video"
    exit 1
fi

# Check if YOLO model exists
if [ ! -f "../yolov8s.pt" ]; then
    echo "Warning: YOLO model not found at ../yolov8s.pt"
    echo "The model will be downloaded automatically on first run"
    echo ""
fi

echo "Starting zone-based detection demo..."
echo ""
echo "Features:"
echo "  • Draw custom detection zones"
echo "  • Get alerts when objects enter zones"
echo "  • Save and load zone configurations"
echo ""
echo "Controls:"
echo "  D - Start/Stop drawing zone"
echo "  C - Complete current zone"
echo "  U - Undo last zone"
echo "  S - Save zones"
echo "  R - Reset all zones"
echo "  Q - Quit"
echo "  SPACE - Pause/Resume"
echo ""
echo "==========================================="
echo ""

# Run the zone detection demo
python3 detect_with_zones.py test-people.mp4

echo ""
echo "==========================================="
echo "Demo completed!"
echo "==========================================="
