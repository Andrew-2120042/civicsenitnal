# Quick Start Guide - CivicSentinel Agent

Get up and running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:

1. ✅ **Node.js 18+**: `node --version`
2. ✅ **Rust**: `rustc --version` (if not: https://rustup.rs)
3. ✅ **Backend API running**: http://localhost:8000/api/v1/health

## Step-by-Step Setup

### 1. Install Dependencies

```bash
cd civicsentinel-agent
npm install
```

This installs:
- React, TypeScript, Vite
- Tauri 2.0
- TailwindCSS, Zustand
- Lucide React icons

### 2. Start Development

```bash
npm run tauri:dev
```

**First launch:**
- Rust compilation takes 2-5 minutes (one-time)
- Subsequent launches are much faster (10-20 seconds)

### 3. Discover Cameras

When the app opens:

1. Click **"Start Scan"**
2. Wait 10-30 seconds for network scan
3. Select cameras with checkboxes
4. Name each camera (optional)
5. Click **"Continue"**

### 4. Connect and Monitor

1. Click **"Connect"** on each camera
2. Click **"Monitor"** to start detection
3. Frames sent to cloud API every 3 seconds

### 5. Create Zones (CRITICAL)

This is the most important feature!

1. Click **"Edit"** button on a camera
2. **Drawing the zone:**
   - Click on the canvas to add points
   - Add at least 3 points
   - Double-click to close the polygon
3. **Configure the zone:**
   - Enter name: "Restricted Area"
   - Select alert type: "Intrusion"
4. Click **"Save Zone"**

### 6. Test Detection

1. Ensure backend API is running
2. Walk in front of camera
3. If YOLO detects you in zone:
   - Desktop notification appears
   - Alert logged in system

## Testing Without Real Cameras

The app includes mock cameras for testing:

1. Click "Start Scan"
2. Mock cameras will appear (192.168.1.100, etc.)
3. Connect to mock cameras
4. They generate placeholder frames
5. Test zone drawing with static images

## Common Issues

### "Network scan found 0 cameras"

**Solution 1**: Use mock cameras (automatically provided)

**Solution 2**: Manually add camera
- Skip discovery screen
- Future: Add manual entry UI

### "Failed to connect to backend"

**Solution**: Start the backend API first
```bash
cd ../civicsentinel  # Go to backend project
poetry run uvicorn app.main:app --reload
```

Verify: http://localhost:8000/api/v1/health

### Rust compilation errors

**macOS**:
```bash
xcode-select --install
```

**Linux (Ubuntu)**:
```bash
sudo apt install libwebkit2gtk-4.1-dev build-essential
```

## Keyboard Shortcuts

- **Cmd/Ctrl + Q**: Quit
- **Cmd/Ctrl + W**: Close window (minimize to tray)
- **Cmd/Ctrl + ,**: Settings (future)

## What's Working

✅ Network scanning (with mock data)
✅ Camera connection
✅ Frame capture
✅ Cloud API integration
✅ **Zone Editor with polygon drawing** ← CRITICAL FEATURE
✅ Zone creation/retrieval
✅ Desktop notifications
✅ System tray integration
✅ State persistence

## What's Next

After basic setup works, you can:

1. **Add Real Cameras**: Use IP Webcam app or RTSP cameras
2. **Define Multiple Zones**: Create zones for different areas
3. **Monitor Live**: Watch real-time detections
4. **Review Alerts**: Check notification history
5. **Configure Settings**: Adjust thresholds, intervals

## Tips

- **Zone Drawing**: Be precise! Use camera frame as reference
- **Frame Rate**: 3-5 seconds is optimal (not too fast, not too slow)
- **API Key**: Use test_api_key_123 for development
- **Performance**: Start with 1-2 cameras, then scale up

## Example Workflow

```
1. Start backend API ✓
2. Run agent: npm run tauri:dev ✓
3. Scan for cameras ✓
4. Select & connect cameras ✓
5. Click "Edit" on first camera ✓
6. Draw polygon zone:
   - Click 4 corners of restricted area
   - Double-click to close
   - Name it "Front Entrance"
   - Save ✓
7. Click "Monitor" ✓
8. Walk in zone → Get alert! ✓
```

## Screenshots

*(Would show here if this were a real deployment)*

1. Camera Discovery Screen
2. Camera List with Live Feeds
3. **Zone Editor (CRITICAL)** - Canvas with polygon drawing
4. Desktop Notification
5. System Tray Icon

## Need Help?

- Check full README.md for detailed docs
- Review code comments in components
- Backend API docs: http://localhost:8000/docs
- GitHub Issues for bugs

---

**You're ready to go!** 🚀

The Zone Editor is the star of the show - have fun drawing zones!
