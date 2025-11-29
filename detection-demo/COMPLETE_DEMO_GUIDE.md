# Complete Zone-Based Detection Demo - User Guide

## Overview

This is a **FULLY FUNCTIONAL** standalone demonstration of zone-based intrusion detection with real-time visual alerts. It combines:

- ✅ Interactive zone drawing
- ✅ Real-time YOLOv8 person detection
- ✅ Zone intrusion detection
- ✅ Visual alert system
- ✅ Professional UI with panels
- ✅ Save/load zone configurations

## Quick Start

```bash
cd /Users/nareshnallabothula/civicsentinal/detection-demo
./run_complete_demo.sh
```

Or run directly:
```bash
python3 detect_with_zones_complete.py test-people.mp4
```

## Visual Interface

When you run the demo, you'll see a professional window with:

```
┌──────────────────────────────────────────────────────────────────┐
│  ⚠️  INTRUSION DETECTED  ⚠️                                       │ ← Alert Banner (Red)
│  Zone 1: 2 person(s)                                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│     [Video with Detection + Zones]                              │
│     • Green boxes = Detected persons                            │
│     • Cyan zones = Normal state                 ┌──────────────┐│
│     • Red zones = Intrusion detected            │ CONTROLS:    ││
│     • Red dots = Drawing points                 │ D - Drawing  ││
│                                                  │ C - Complete ││
│   ┌────────────┐                                │ U - Undo     ││
│   │ Frame: 25  │                                │ R - Reset    ││
│   │ Zones: 2   │                                │ S - Save     ││
│   │ Status:    │                                │ SPACE-Pause  ││
│   │ ALERT!     │                                │ Q - Quit     ││
│   └────────────┘                                └──────────────┘│
│                                                                  │
│  DRAWING MODE - Click to add points (3 points)                  │ ← Drawing Indicator
└──────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Usage

### 1. Launch the Demo

Run the demo and a window will open showing the video playing with person detection active.

### 2. Draw Your First Zone

**Step 1**: Press `D` to enter drawing mode
- You'll see "DRAWING MODE" indicator at the bottom
- The video continues playing

**Step 2**: Click on the video to mark zone corners
- Each click adds a point (shown as a RED DOT)
- Lines connect the points (shown in CYAN)
- You need at least 3 points to create a zone
- Tip: Press SPACE to pause the video first for easier drawing

**Step 3**: Press `C` to complete the zone
- The zone becomes active
- Shows as a semi-transparent CYAN overlay
- Zone label appears (e.g., "ZONE 1")
- Drawing mode automatically exits

### 3. Watch for Intrusions

Once a zone is drawn, the system monitors it in real-time:

**Normal State:**
- Zone appears in CYAN color
- Video plays normally
- Persons are detected with GREEN boxes

**Intrusion Detected:**
- Zone turns RED
- Large RED ALERT BANNER appears at top
- Banner shows: "⚠️ INTRUSION DETECTED ⚠️"
- Details show: "Zone 1: 2 person(s)"
- Alert stays active as long as person is in zone

### 4. Multiple Zones

You can draw multiple zones:

1. Press `D` to start drawing again
2. Click points for the second zone
3. Press `C` to complete
4. Repeat for more zones

Each zone is numbered (Zone 1, Zone 2, etc.) and monitored independently.

### 5. Save Your Configuration

Press `S` to save zones to `zones_config.json`

The file is saved in the demo directory and looks like:
```json
[
  [
    [100, 200],
    [300, 200],
    [300, 400],
    [100, 400]
  ]
]
```

Next time you run the demo, these zones load automatically!

## Keyboard Controls Reference

| Key | Action | Description |
|-----|--------|-------------|
| **D** | Toggle Drawing Mode | Start/stop drawing zones |
| **C** | Complete Zone | Finish current zone (min 3 points) |
| **U** | Undo Last Zone | Remove the most recent zone |
| **R** | Reset All Zones | Clear all zones and start over |
| **S** | Save Zones | Save to zones_config.json |
| **SPACE** | Pause/Resume | Pause video for easier drawing |
| **Q** | Quit | Exit the demo |

## Visual Elements Explained

### Colors

**Zone Colors:**
- 🟦 **CYAN** = Normal zone (no intrusion)
- 🟥 **RED** = Alert zone (intrusion detected)

**Detection Colors:**
- 🟩 **GREEN** = Person detected (bounding box)
- 🔴 **RED** = Drawing points
- 🟦 **CYAN** = Drawing lines

**UI Colors:**
- 🟥 **RED** = Alert banner background
- ⬛ **DARK GRAY** = Info panels

### On-Screen Panels

**Info Panel (Bottom-Left):**
- Current frame number
- Total zones created
- Current mode (Drawing/Monitoring)
- Alert status
- Total intrusions counted

**Controls Panel (Top-Right):**
- Complete keyboard reference
- Always visible for easy reference

### Detection Features

**Bounding Boxes:**
- Draw around detected persons
- Show class name and confidence
- Green dot shows center point (used for zone checking)

**Zone Detection:**
- Checks if person's CENTER is inside zone
- Updates every frame in real-time
- Multiple persons can trigger same zone

## Tips & Best Practices

### Drawing Zones

1. **Pause First**: Press SPACE to pause video, makes drawing easier
2. **Strategic Placement**: Draw zones where you expect activity
3. **Size Matters**: Larger zones catch more activity
4. **Simple Shapes**: Rectangles work great, don't overcomplicate
5. **Test Immediately**: Resume video after drawing to test the zone

### Example Zone Placements

**Doorway Monitor:**
```
Draw a rectangle around the door entrance
Alert when someone walks through
```

**Restricted Area:**
```
Draw polygon around off-limits space
Get alerts for any entry
```

**Path Monitor:**
```
Draw zone along walkway
Track movement patterns
```

**Multi-Zone Setup:**
```
Zone 1: Entrance
Zone 2: Restricted area
Zone 3: Exit
Monitor entire workflow
```

### Performance Tips

1. **Confidence Threshold**: Default is 0.5
   - Lower (0.3) = More detections, more false positives
   - Higher (0.7) = Fewer detections, more reliable

2. **Zone Count**: You can create many zones, but:
   - More zones = more CPU usage
   - Keep to 3-5 zones for best performance

3. **Video Quality**: Higher resolution = slower processing

## Use Cases

### 1. Security Monitoring
Draw zones around entrances, restricted areas, or valuable assets.

### 2. Workflow Analysis
Monitor how people move through spaces by creating sequential zones.

### 3. Occupancy Tracking
Create zones for different areas to count people in each section.

### 4. Demonstration
Show clients or stakeholders how zone-based detection works.

### 5. Testing
Test detection algorithms and zone configurations before deployment.

## Troubleshooting

**Problem:** Window doesn't open
- **Solution**: Check if running over SSH, may need display forwarding

**Problem:** No detections appearing
- **Solution**: Lower confidence with `--confidence 0.3`

**Problem:** Zones not detecting
- **Solution**: Make sure person's CENTER (green dot) enters the zone
- **Solution**: Try larger zones for testing

**Problem:** Can't draw zone
- **Solution**: Make sure you pressed 'D' first to enter drawing mode
- **Solution**: Need at least 3 points before pressing 'C'

**Problem:** Drawing points in wrong place
- **Solution**: Press SPACE to pause video first
- **Solution**: Draw slowly and deliberately

**Problem:** Zones not saving
- **Solution**: Check write permissions in the demo directory
- **Solution**: Look for error messages when pressing 'S'

## Advanced Usage

### Custom Video

Use your own video file:
```bash
python3 detect_with_zones_complete.py /path/to/your/video.mp4
```

### Adjust Confidence

See more or fewer detections:
```bash
# More detections (lower threshold)
python3 detect_with_zones_complete.py test-people.mp4 --confidence 0.3

# Fewer detections (higher threshold)
python3 detect_with_zones_complete.py test-people.mp4 --confidence 0.7
```

### Different Model

Use a different YOLO model:
```bash
python3 detect_with_zones_complete.py test-people.mp4 --model yolov8n.pt
```

Models:
- `yolov8n.pt` - Nano (fastest)
- `yolov8s.pt` - Small (default, balanced)
- `yolov8m.pt` - Medium (more accurate)
- `yolov8l.pt` - Large (most accurate)

### Reuse Zones

Zones save to `zones_config.json` and load automatically:

```bash
# Create zones with one video
python3 detect_with_zones_complete.py video1.mp4
# Draw zones, press 'S' to save

# Use same zones with different video
python3 detect_with_zones_complete.py video2.mp4
# Zones load automatically
```

## What This Demonstrates

This demo shows ALL key components of a production surveillance system:

1. **Zone Configuration**: How operators define monitoring areas
2. **Real-Time Detection**: How AI identifies people in video
3. **Intrusion Logic**: How system determines when to alert
4. **Visual Feedback**: How operators see detections and alerts
5. **Configuration Management**: How settings are saved and loaded
6. **Multi-Zone Support**: How multiple areas are monitored
7. **Status Tracking**: How system tracks alerts and statistics

## Technical Details

### Detection Algorithm
- **Model**: YOLOv8 (You Only Look Once)
- **Classes**: Detects 80 object types (focuses on "person")
- **Speed**: ~10-30 FPS depending on hardware
- **Accuracy**: Confidence threshold filtering

### Zone Algorithm
- **Method**: Point-in-polygon ray casting
- **Check**: Person's bounding box center
- **Update**: Every frame
- **Performance**: O(n) per zone per detection

### Architecture
```
Video Frame → YOLO Detection → Extract Persons →
Check Centers vs Zones → Update Alerts → Draw UI → Display
```

## Next Steps

After mastering this demo, you can:

1. **Apply to CivicSentinel**: Use these concepts in the main project
2. **Test Different Scenarios**: Try various videos and zone layouts
3. **Understand Limitations**: Learn what works and what doesn't
4. **Design Production System**: Plan how to build a real deployment

## Files Created

- `detect_with_zones_complete.py` - Main demo script (complete)
- `run_complete_demo.sh` - One-click launcher
- `COMPLETE_DEMO_GUIDE.md` - This guide
- `zones_config.json` - Saved zones (created when you press 'S')

## Summary

This is a **complete, production-quality demonstration** of zone-based detection:

✅ Fully functional zone drawing
✅ Real-time person detection
✅ Intrusion alerts with visual feedback
✅ Professional UI with panels
✅ Save/load configurations
✅ Multiple zones support
✅ Complete keyboard controls

Everything works exactly as it would in a real surveillance system!

---

**Ready to try it? Run:** `./run_complete_demo.sh`
