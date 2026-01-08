#!/bin/bash

# Complete Zone-Based Detection Demo Launcher

clear

cat << "EOF"
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║    ZONE-BASED DETECTION DEMO - COMPLETE VERSION                     ║
║                                                                      ║
║    Interactive demonstration of zone drawing + detection + alerts   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
EOF

echo ""
echo "Checking requirements..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3 is not installed"
    exit 1
fi
echo "✓ Python3 found: $(python3 --version)"

# Check packages
echo "✓ Checking required packages..."
python3 -c "import cv2; import ultralytics; import numpy" 2>/dev/null

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Some packages are missing. Installing..."
    pip install opencv-python ultralytics numpy
    echo ""
fi

# Check video
if [ ! -f "test-people.mp4" ]; then
    echo "✗ test-people.mp4 not found"
    echo "  Please make sure the video file exists in this directory"
    exit 1
fi
echo "✓ Video file found"

# Check model
if [ ! -f "../yolov8s.pt" ]; then
    echo "⚠ YOLO model not found at ../yolov8s.pt"
    echo "  Model will be downloaded automatically on first run"
    echo ""
fi

echo ""
echo "══════════════════════════════════════════════════════════════════════"
echo ""
echo "  FEATURES:"
echo "  • Draw custom detection zones with mouse"
echo "  • Real-time person detection with bounding boxes"
echo "  • Visual alerts when person enters zone"
echo "  • Save/load zone configurations"
echo "  • Professional visual interface"
echo ""
echo "  KEYBOARD CONTROLS:"
echo "  • D      - Start/Stop drawing zone"
echo "  • C      - Complete current zone (min 3 points)"
echo "  • U      - Undo last zone"
echo "  • R      - Reset all zones"
echo "  • S      - Save zones to file"
echo "  • SPACE  - Pause/Resume video"
echo "  • Q      - Quit demo"
echo ""
echo "══════════════════════════════════════════════════════════════════════"
echo ""
read -p "Press ENTER to start the demo..."

echo ""
echo "Starting demo..."
echo ""

# Run the complete demo
python3 detect_with_zones_complete.py test-people.mp4

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║    Demo completed! Thank you for trying the zone detection demo.    ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
