# CivicSentinel Desktop Agent

AI-powered CCTV monitoring desktop application built with Tauri 2.0, React, and TypeScript.

## Features

✅ **Network Camera Discovery** - Automatically scan and find IP cameras on your network
✅ **RTSP Connection** - Connect to IP cameras via RTSP streams
✅ **Zone Editor** - Visual polygon drawing tool to define restricted areas (CRITICAL FEATURE)
✅ **Real-time Detection** - Send frames to cloud API for person detection
✅ **Zone Monitoring** - Alert when persons detected in restricted zones
✅ **Desktop Notifications** - Native OS notifications for alerts
✅ **System Tray** - Runs in background with system tray integration
✅ **State Management** - Persistent storage with Zustand

## Architecture

```
Tauri Desktop App
├── Rust Backend (src-tauri/)
│   ├── Camera Discovery (network scanning)
│   ├── RTSP Frame Capture
│   ├── Cloud API Integration
│   ├── System Tray
│   └── Desktop Notifications
│
└── React Frontend (src/)
    ├── Camera Discovery UI
    ├── Camera List & Monitoring
    ├── Zone Editor (Canvas-based polygon drawing) ← CRITICAL
    ├── Settings Management
    └── Zustand State Stores
```

## Prerequisites

- **Node.js** 18+ and npm
- **Rust** 1.70+ (install from https://rustup.rs)
- **Tauri CLI** 2.0+
- **Backend API** running on http://localhost:8000 (from civicsentinel project)

### Platform-specific Requirements

**macOS:**
```bash
xcode-select --install
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev \
    build-essential \
    curl \
    wget \
    file \
    libssl-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

**Windows:**
- Install Microsoft C++ Build Tools
- Install WebView2 (usually pre-installed on Windows 10/11)

## Installation

1. **Clone and navigate:**
   ```bash
   cd civicsentinel-agent
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development mode:**
   ```bash
   npm run tauri:dev
   ```

## Usage

### First Launch - Camera Discovery

1. Click "Start Scan" to discover cameras on your network
2. Select cameras you want to monitor
3. Name each camera (e.g., "Front Gate", "Parking Lot")
4. Click "Continue"

### Monitoring Cameras

1. Click "Connect" on each camera card
2. Click "Monitor" to start sending frames to cloud
3. Live thumbnails update every 3 seconds
4. Click "Edit Zones" to define restricted areas

### Zone Editor (CRITICAL FEATURE)

The Zone Editor is the most important feature - it allows drawing restricted areas:

**How to Use:**
1. Click "Edit" button on a camera
2. See your camera feed as background
3. **Click** on canvas to add polygon points
4. Minimum 3 points required
5. **Double-click** to close the polygon
6. Enter zone name (e.g., "Restricted Area")
7. Select alert type (Intrusion/Loitering/Counting)
8. Click "Save Zone"

**Drawing Tips:**
- Red dots show each point
- Lines connect the points automatically
- Semi-transparent fill shows the zone area
- Existing zones appear in green
- Selected zones appear in blue

### Desktop Notifications

When a person is detected in a restricted zone:
- Native OS notification appears
- Title: "🚨 CivicSentinel Alert"
- Body: "{alert_type} detected at {camera_name}"
- Click notification to open app

### System Tray

- App minimizes to system tray
- Click tray icon to show/hide window
- Right-click for menu:
  - "Monitoring: ON/OFF" - Toggle monitoring
  - "Settings"
  - "Quit"

## Configuration

Edit in the app's Settings page (or `~/.config/civicsentinel-agent/` on Linux):

```json
{
  "backendUrl": "http://localhost:8000",
  "apiKey": "test_api_key_123",
  "enableNotifications": true,
  "enableSound": true,
  "confidenceThreshold": 0.5
}
```

## Project Structure

```
civicsentinel-agent/
├── src-tauri/
│   ├── src/
│   │   ├── main.rs              # Tauri entry point, commands
│   │   ├── camera.rs            # Camera discovery & frame capture
│   │   ├── api.rs               # Cloud API communication
│   │   └── build.rs             # Build script
│   ├── Cargo.toml               # Rust dependencies
│   └── tauri.conf.json          # Tauri configuration
│
├── src/
│   ├── components/
│   │   ├── CameraDiscovery.tsx  # Network scanner UI
│   │   ├── CameraList.tsx       # Camera grid & monitoring
│   │   └── ZoneEditor.tsx       # Polygon drawing (CRITICAL)
│   ├── stores/
│   │   ├── cameraStore.ts       # Camera state management
│   │   ├── authStore.ts         # Authentication state
│   │   ├── settingsStore.ts     # App settings
│   │   └── alertStore.ts        # Alert history
│   ├── lib/
│   │   └── types.ts             # TypeScript types
│   ├── App.tsx                  # Main app component
│   ├── main.tsx                 # React entry point
│   └── index.css                # Global styles
│
├── package.json                 # Node dependencies
├── vite.config.ts               # Vite configuration
├── tsconfig.json                # TypeScript config
├── tailwind.config.js           # Tailwind CSS config
└── README.md                    # This file
```

## Development

### Run in Development Mode

```bash
npm run tauri:dev
```

This will:
- Start Vite dev server (React)
- Compile Rust backend
- Launch Tauri window
- Enable hot-reload for frontend changes

### Build for Production

```bash
npm run tauri:build
```

Outputs:
- **macOS**: `src-tauri/target/release/bundle/dmg/`
- **Windows**: `src-tauri/target/release/bundle/msi/`
- **Linux**: `src-tauri/target/release/bundle/deb/` or `appimage/`

## API Integration

The agent connects to the CivicSentinel backend API:

### Endpoints Used

1. **POST /api/v1/detect**
   - Sends camera frames for person detection
   - Multipart form: `image` (JPEG bytes), `camera_id`
   - Returns: detections + zone alerts

2. **POST /api/v1/cameras/{id}/zones**
   - Creates restricted zones
   - Body: `name`, `coordinates` (polygon), `alert_type`

3. **GET /api/v1/cameras/{id}/zones**
   - Retrieves existing zones

### Authentication

Uses Bearer token authentication:
```
Authorization: Bearer {api_key}
```

Default test key: `test_api_key_123`

## Testing

### Test with Phone Camera

1. Install "IP Webcam" app on Android
2. Start server in app
3. Note RTSP URL (e.g., `rtsp://192.168.1.50:8080/h264`)
4. In agent, scan network or manually enter URL
5. Connect and start monitoring

### Test with Mock Camera

The Rust backend includes mock camera support for testing without real cameras.

## Troubleshooting

### "Failed to scan network"

- Ensure you're on the same network as cameras
- Check firewall settings
- Try manual RTSP URL entry

### "Failed to connect camera"

- Verify RTSP URL is correct
- Check camera credentials (if required)
- Ensure camera supports RTSP

### "API error 401/403"

- Check API key is correct
- Verify backend is running on http://localhost:8000
- Check camera limit for your plan

### Build Errors

**macOS:** Install Xcode Command Line Tools
```bash
xcode-select --install
```

**Linux:** Install required dependencies (see Prerequisites)

**Windows:** Ensure WebView2 is installed

## Performance

- **Frame Rate**: 5 FPS (one frame every 3 seconds per camera)
- **Network Usage**: ~50-100 KB per frame
- **CPU Usage**: Low (offloads detection to cloud API)
- **Memory**: ~200-300 MB per camera

## Security

- API keys stored in OS-secure storage
- RTSP credentials transmitted securely
- No frame data stored locally (sent to cloud only)

## Roadmap

- [ ] Settings page UI
- [ ] Alerts history view
- [ ] Video recording
- [ ] Multiple zone types (loitering detection)
- [ ] Audio notifications
- [ ] Multi-camera sync
- [ ] Offline mode

## Contributing

This is part of the CivicSentinel project. See main project for contribution guidelines.

## License

MIT License - See LICENSE file

## Support

- GitHub Issues: https://github.com/yourusername/civicsentinel/issues
- Email: support@civicsentinel.com

---

**Built with**: Tauri 2.0, React 18, TypeScript, Rust, TailwindCSS, Zustand

**Critical Component**: Zone Editor with canvas-based polygon drawing 🎯
