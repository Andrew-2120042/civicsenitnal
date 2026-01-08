# Zone-Based Detection Demo Guide

## Overview

This is a **fully functional demo** showing how zone-based intrusion detection works with YOLO object detection. You can:

- **Draw custom detection zones** on the video
- **Get real-time alerts** when people/objects enter zones
- **See visual feedback** with bounding boxes and alerts
- **Save and load zone configurations** for reuse

## Quick Start

```bash
cd /Users/nareshnallabothula/civicsentinal/detection-demo
./run_zone_demo.sh
```

Or run manually:
```bash
python3 detect_with_zones.py test-people.mp4
```

## Features

### 1. Interactive Zone Drawing
- Click to add points and create custom polygonal zones
- Draw multiple zones in different areas
- Zones can be any shape (triangle, rectangle, pentagon, etc.)

### 2. Real-Time Intrusion Detection
- Detects when objects (people, cars, etc.) enter zones
- Uses bounding box center point for zone checking
- Works with all YOLO-detected object classes

### 3. Visual Alerts
- **Red alert banner** appears at top when intrusion detected
- Shows which zone has intrusion and what was detected
- **Zone highlighting**: Zones turn red when objects are inside
- **Bounding boxes**: Green for persons, blue for cars, etc.

### 4. Zone Management
- Save zones to JSON file for reuse
- Load previously saved zones automatically
- Undo zones if you make mistakes
- Reset all zones to start over

## How to Use

### Step 1: Run the Demo

```bash
python3 detect_with_zones.py test-people.mp4
```

The video will start playing with detection enabled.

### Step 2: Draw Your First Zone

1. **Press 'D'** to enter drawing mode
   - You'll see "DRAWING MODE - Click to add points" at the bottom

2. **Click on the video** to add zone boundary points
   - Click at least 3 points to create a zone
   - Points will appear as yellow dots
   - Lines connect the points as you draw

3. **Press 'C'** to complete the zone
   - The zone becomes a polygon and is now active
   - Drawing mode turns off automatically

### Step 3: Watch for Intrusions

- When a person/object enters your zone:
  - **Red alert banner** appears at top
  - Shows "INTRUSION DETECTED!"
  - Lists what was detected in which zone
  - Zone turns from magenta to red

### Step 4: Save Your Zones

- **Press 'S'** to save zones to `zones_config.json`
- Zones will load automatically next time you run the demo

## Controls

| Key | Action |
|-----|--------|
| **D** | Start/Stop drawing zone |
| **C** | Complete current zone (needs 3+ points) |
| **U** | Undo last zone |
| **S** | Save zones to file |
| **R** | Reset all zones |
| **Q** | Quit demo |
| **SPACE** | Pause/Resume video |

## Visual Guide

### Colors Explained

**Zone Colors:**
- **Magenta (normal)**: Zone with no detections
- **Red (alert)**: Zone with intrusion detected

**Bounding Box Colors:**
- **Green**: Person detected
- **Blue**: Car detected
- **Orange**: Truck detected
- **Yellow**: Other objects

**Drawing Colors:**
- **Cyan**: Zone being drawn (lines and points)

### Screen Layout

```
┌─────────────────────────────────────────────┐
│ [RED BANNER - INTRUSION DETECTED!]          │ ← Alert when intrusion
│ Zone 1: 2 person                            │
├─────────────────────────────────────────────┤
│ Frame: 150/596                              │ ← Frame counter
│                                             │
│   [Video with detections and zones]         │
│   • Bounding boxes around detected objects  │
│   • Magenta/Red zones drawn on video        │
│   • Zone labels (Zone 1, Zone 2, etc.)      │
│                                             │
│                              ┌──────────────┐│
│                              │ Controls:    ││ ← Instructions panel
│                              │ D - Draw     ││
│                              │ C - Complete ││
│                              │ U - Undo     ││
│                              │ S - Save     ││
│                              │ R - Reset    ││
│                              │ Q - Quit     ││
│                              │ SPACE - Pause││
│                              └──────────────┘│
│ [DRAWING MODE - Click to add points]        │ ← Drawing indicator
└─────────────────────────────────────────────┘
```

## Example Scenarios

### Scenario 1: Doorway Monitoring

**Goal**: Alert when someone enters through a door

1. Run the demo
2. Press 'D' to start drawing
3. Click around the doorway area (4 points for rectangle)
4. Press 'C' to complete
5. Watch for alerts when people walk through

### Scenario 2: Restricted Area

**Goal**: Detect entry into a restricted zone

1. Draw a zone around the restricted area
2. The system alerts when anyone enters
3. Multiple zones can be monitored simultaneously

### Scenario 3: Perimeter Security

**Goal**: Monitor the edges of the frame

1. Draw zones along the perimeter
2. Get alerts when objects appear at edges
3. Save configuration for reuse

## Technical Details

### Zone Detection Algorithm

- **Point-in-polygon test**: Uses ray casting algorithm
- **Detection point**: Center of bounding box
- **Update frequency**: Every frame (real-time)
- **Multi-zone support**: Unlimited zones

### Performance

- **FPS**: Depends on video and hardware
- **Detection confidence**: Default 0.5 (50%)
- **Adjustable**: Use `--confidence` flag

### File Format

Zones are saved in `zones_config.json`:

```json
[
  [
    [100, 200],
    [300, 200],
    [300, 400],
    [100, 400]
  ],
  [
    [500, 100],
    [600, 150],
    [550, 250]
  ]
]
```

Each zone is a list of [x, y] coordinate pairs.

## Tips and Tricks

### Drawing Tips

1. **Pause first**: Press SPACE to pause, makes drawing easier
2. **Start at top-left**: Work clockwise for clean zones
3. **Don't cross lines**: Keep zone boundaries simple
4. **Test immediately**: Draw, complete, then resume video to test

### Detection Tips

1. **Lower confidence for more detections**: `--confidence 0.3`
2. **Higher confidence for fewer false positives**: `--confidence 0.7`
3. **Zone size matters**: Larger zones catch more activity
4. **Center-based**: Only center of object needs to be in zone

### Workflow Tips

1. **Save often**: Press 'S' after creating good zones
2. **Undo mistakes**: Press 'U' immediately if zone is wrong
3. **Multiple attempts**: Press 'R' to reset and start over
4. **Test different videos**: Works with any video file

## Advanced Usage

### Custom Video

```bash
python3 detect_with_zones.py /path/to/your/video.mp4
```

### Different Model

```bash
python3 detect_with_zones.py video.mp4 --model /path/to/yolov8n.pt
```

### Adjust Confidence

```bash
python3 detect_with_zones.py video.mp4 --confidence 0.7
```

### Reuse Saved Zones

Zones saved in `zones_config.json` load automatically. To use with different video:

```bash
# Create zones with one video
python3 detect_with_zones.py video1.mp4
# Press 'S' to save zones

# Use same zones with different video
python3 detect_with_zones.py video2.mp4
# Zones load automatically
```

## Troubleshooting

**Zones not saving?**
- Check write permissions in demo directory
- Look for `zones_config.json` file after pressing 'S'

**No detections appearing?**
- Lower confidence threshold: `--confidence 0.3`
- Check if objects are in frame

**Zones not detecting?**
- Make sure object's CENTER enters zone, not just edge
- Try larger zones for testing

**Video won't open?**
- Verify file path is correct
- Supported formats: .mp4, .avi, .mov, .mkv

**Drawing not working?**
- Make sure to press 'D' first to enable drawing mode
- Check for "DRAWING MODE" message at bottom

## What This Demonstrates

This demo showcases the core functionality that would be used in a production surveillance system:

1. **Zone Configuration**: How operators define areas of interest
2. **Real-time Detection**: How AI detects objects in video
3. **Intrusion Logic**: How system determines if alert is needed
4. **Visual Feedback**: How operators see what's happening
5. **Configuration Management**: How settings are saved/loaded

## Differences from Production System

This is a **demonstration** - a real production system would also include:

- Database storage of events
- Alert notifications (email, SMS, etc.)
- Multi-camera support
- Cloud recording
- Web dashboard
- User authentication
- Event timeline
- Playback controls

But the **core detection and zone logic** shown here is exactly how it works!

## Next Steps

After trying this demo, you'll understand:
- How zone-based detection works
- How to configure detection areas
- How intrusion alerts are triggered
- The capabilities and limitations of YOLO detection

You can then apply these concepts to:
- Building a full surveillance system
- Integrating with cameras
- Creating custom alert rules
- Developing a production application

Enjoy exploring zone-based detection!
