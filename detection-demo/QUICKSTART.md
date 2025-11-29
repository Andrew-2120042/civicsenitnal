# Quick Start Guide - Detection Demo

## Fastest Way to Run

```bash
cd /Users/nareshnallabothula/civicsentinal/detection-demo
./run_demo.sh
```

That's it! The script will handle everything automatically.

## What You'll See

A window will open showing your video with:
- **Bounding boxes** around detected objects
- **Labels** showing object type (person, car, etc.)
- **Confidence scores** (e.g., "0.85" = 85% confident)
- **Frame counter** in top-left
- **Detection count** in top-left

## Manual Run

If you prefer to run manually:

```bash
# Basic run
python3 detect_video.py sample-video.mp4

# Save output video
python3 detect_video.py sample-video.py --output detected-output.mp4

# Adjust confidence threshold
python3 detect_video.py sample-video.mp4 --confidence 0.7
```

## Using Your Own Video

```bash
# Copy your video to this folder
cp /path/to/your/video.mp4 ./my-video.mp4

# Run detection
python3 detect_video.py my-video.mp4
```

## Colors Explained

- **Green boxes** = Person detected
- **Blue boxes** = Car detected
- **Orange boxes** = Truck detected
- **Yellow boxes** = Other objects

## Keyboard Controls

- **Q** = Quit
- **P** = Pause/Resume
- **S** = Save current frame as image

## Example Output

At the end, you'll see stats like:

```
==================================================
Detection Statistics:
==================================================
person: 156 detections
car: 23 detections
truck: 5 detections
==================================================
```

## Tips

1. **High confidence only**: Use `--confidence 0.8` to see only very confident detections
2. **Save output**: Use `--output result.mp4` to save the annotated video
3. **Pause to examine**: Press 'P' to pause and look closely at detections
4. **Save interesting frames**: Press 'S' to save any frame as an image

## Troubleshooting

**Import errors?**
```bash
pip install opencv-python ultralytics numpy
```

**Video won't play?**
- Check file path is correct
- Supported: .mp4, .avi, .mov, .mkv

**Too slow?**
- Use lower resolution video
- Or adjust confidence threshold higher

## Files in This Demo

- `detect_video.py` - Main detection script
- `sample-video.mp4` - Sample pedestrian video
- `run_demo.sh` - One-click launcher
- `README.md` - Detailed documentation
- `QUICKSTART.md` - This file

Enjoy exploring object detection!
