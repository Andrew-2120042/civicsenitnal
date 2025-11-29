use serde::{Deserialize, Serialize};
use std::net::IpAddr;
use std::time::Duration;
use std::process::Command;
use std::sync::Arc;
use tokio::sync::Mutex;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveredCamera {
    pub ip: String,
    pub rtsp_url: String,
    pub status: String,
    pub port: u16,
}

#[derive(Debug, Clone)]
pub enum CameraSource {
    Rtsp(String),
    VideoFile { path: String, current_frame: usize },
}

#[derive(Debug, Clone)]
pub struct CameraHandle {
    pub source: Arc<Mutex<CameraSource>>,
    pub is_connected: bool,
}

/// Scan local network for IP cameras
pub async fn scan_for_cameras() -> Result<Vec<DiscoveredCamera>, String> {
    println!("[Camera] Starting network scan...");

    let mut discovered_cameras = Vec::new();

    // Get local IP to determine subnet
    let local_ip = local_ip_address::local_ip()
        .map_err(|e| format!("Failed to get local IP: {}", e))?;

    println!("[Camera] Local IP: {}", local_ip);

    // For demo: Add mock cameras for testing
    // In production, this would scan the network
    discovered_cameras.push(DiscoveredCamera {
        ip: "192.168.1.100".to_string(),
        rtsp_url: "rtsp://192.168.1.100:554/live".to_string(),
        status: "discovered".to_string(),
        port: 554,
    });

    // Real network scanning logic would go here
    // This would:
    // 1. Parse local IP to get subnet (e.g., 192.168.1.0/24)
    // 2. Scan common camera ports (554, 8554, 8080) on each IP
    // 3. Try to connect and verify it's a camera
    // 4. Return list of discovered cameras

    let subnet = match local_ip {
        IpAddr::V4(ip) => {
            let octets = ip.octets();
            // Example: if IP is 192.168.1.50, scan 192.168.1.0/24
            format!("{}.{}.{}", octets[0], octets[1], octets[2])
        }
        _ => return Ok(discovered_cameras),
    };

    println!("[Camera] Scanning subnet: {}.x", subnet);

    // Scan a subset of IPs (would be full range in production)
    for i in 1..=254 {
        if i > 10 && i < 245 {
            // Skip most IPs for demo speed
            continue;
        }

        let ip = format!("{}.{}", subnet, i);

        // Try common RTSP ports
        for port in [554, 8554] {
            let rtsp_url = format!("rtsp://{}:{}/live", ip, port);

            // Quick check (would actually test connection in production)
            // For now, just add potential cameras
            if i % 10 == 0 {
                // Mock: every 10th IP is a "camera"
                discovered_cameras.push(DiscoveredCamera {
                    ip: ip.clone(),
                    rtsp_url,
                    status: "discovered".to_string(),
                    port,
                });
            }
        }
    }

    println!("[Camera] Found {} potential cameras", discovered_cameras.len());

    Ok(discovered_cameras)
}

/// Test if a camera connection works
pub async fn test_camera_connection(rtsp_url: &str) -> Result<bool, String> {
    println!("[Camera] Testing connection to: {}", rtsp_url);

    // In production, this would:
    // 1. Try to connect to RTSP stream
    // 2. Attempt to read a frame
    // 3. Return true if successful

    // For now, simulate by checking URL format
    if rtsp_url.starts_with("rtsp://") {
        // Simulate network delay
        tokio::time::sleep(Duration::from_millis(500)).await;
        Ok(true)
    } else {
        Err("Invalid RTSP URL".to_string())
    }
}

/// Connect to a camera or video file
pub async fn connect(source_url: &str) -> Result<CameraHandle, String> {
    println!("[Camera] Connecting to: {}", source_url);
    println!("[Camera] URL ends with .mp4? {}", source_url.ends_with(".mp4"));
    println!("[Camera] URL ends with .mkv? {}", source_url.ends_with(".mkv"));

    let source = if source_url.starts_with("rtsp://") {
        // RTSP stream
        println!("[Camera] Detected RTSP stream");
        CameraSource::Rtsp(source_url.to_string())
    } else if source_url.ends_with(".mp4") || source_url.ends_with(".avi") || source_url.ends_with(".mov") || source_url.ends_with(".mkv") {
        // Video file
        println!("[Camera] Detected video file");
        let path = if source_url.starts_with("file://") {
            source_url.strip_prefix("file://").unwrap().to_string()
        } else {
            source_url.to_string()
        };

        println!("[Camera] Checking if file exists at: {}", path);
        // Check if file exists
        if !std::path::Path::new(&path).exists() {
            println!("[Camera] ERROR: File not found!");
            return Err(format!("Video file not found: {}", path));
        }

        println!("[Camera] Using video file: {}", path);
        CameraSource::VideoFile {
            path,
            current_frame: 0,
        }
    } else {
        // Default to RTSP for backward compatibility
        println!("[Camera] No match found, defaulting to RTSP");
        CameraSource::Rtsp(source_url.to_string())
    };

    Ok(CameraHandle {
        source: Arc::new(Mutex::new(source)),
        is_connected: true,
    })
}

/// Capture a single frame from camera or video file
pub async fn capture_frame(handle: &CameraHandle) -> Result<Vec<u8>, String> {
    if !handle.is_connected {
        return Err("Camera not connected".to_string());
    }

    let mut source = handle.source.lock().await;

    match &mut *source {
        CameraSource::Rtsp(_url) => {
            // For RTSP streams, generate placeholder image
            // In production, this would capture from actual RTSP stream
            let img = image::ImageBuffer::from_fn(640, 480, |x, y| {
                let r = (x as f32 / 640.0 * 255.0) as u8;
                let g = (y as f32 / 480.0 * 255.0) as u8;
                let b = 128;
                image::Rgb([r, g, b])
            });

            let mut bytes: Vec<u8> = Vec::new();
            let mut cursor = std::io::Cursor::new(&mut bytes);

            img.write_to(&mut cursor, image::ImageFormat::Jpeg)
                .map_err(|e| format!("Failed to encode image: {}", e))?;

            Ok(bytes)
        }
        CameraSource::VideoFile { path, current_frame } => {
            // Extract frame using ffmpeg
            let frame_num = *current_frame;
            *current_frame += 1;  // Increment for next call

            // Use ffmpeg to extract specific frame
            // Try common ffmpeg locations
            let ffmpeg_path = if std::path::Path::new("/opt/homebrew/bin/ffmpeg").exists() {
                "/opt/homebrew/bin/ffmpeg"
            } else if std::path::Path::new("/usr/local/bin/ffmpeg").exists() {
                "/usr/local/bin/ffmpeg"
            } else {
                "ffmpeg" // Fallback to PATH
            };

            let output = Command::new(ffmpeg_path)
                .args(&[
                    "-i", path,
                    "-vf", &format!("select=eq(n\\,{}),scale=960:-1", frame_num),  // Resize to 960px width - better quality
                    "-frames:v", "1",
                    "-f", "image2pipe",
                    "-vcodec", "mjpeg",
                    "-q:v", "5",  // Better quality (1=best, 31=worst)
                    "-",
                ])
                .output()
                .map_err(|e| format!("Failed to run ffmpeg: {}. Make sure ffmpeg is installed.", e))?;

            if !output.status.success() {
                // If we've gone past the end of video, loop back to start
                *current_frame = 0;
                return capture_frame_at_position(path, 0);
            }

            Ok(output.stdout)
        }
    }
}

/// Helper function to capture frame at specific position
fn capture_frame_at_position(video_path: &str, frame_num: usize) -> Result<Vec<u8>, String> {
    // Try common ffmpeg locations
    let ffmpeg_path = if std::path::Path::new("/opt/homebrew/bin/ffmpeg").exists() {
        "/opt/homebrew/bin/ffmpeg"
    } else if std::path::Path::new("/usr/local/bin/ffmpeg").exists() {
        "/usr/local/bin/ffmpeg"
    } else {
        "ffmpeg" // Fallback to PATH
    };

    let output = Command::new(ffmpeg_path)
        .args(&[
            "-i", video_path,
            "-vf", &format!("select=eq(n\\,{}),scale=960:-1", frame_num),  // Resize to 960px width - better quality
            "-frames:v", "1",
            "-f", "image2pipe",
            "-vcodec", "mjpeg",
            "-q:v", "5",  // Better quality (1=best, 31=worst)
            "-",
        ])
        .output()
        .map_err(|e| format!("Failed to run ffmpeg: {}", e))?;

    if !output.status.success() {
        return Err(format!("ffmpeg failed: {}", String::from_utf8_lossy(&output.stderr)));
    }

    Ok(output.stdout)
}

// Production implementation notes:
//
// For real RTSP capture, you would use:
//
// Option 1: FFmpeg (via std::process::Command)
// ```
// ffmpeg -i rtsp://camera/stream -vframes 1 -f image2pipe -
// ```
//
// Option 2: GStreamer (via gstreamer-rs)
// ```rust
// use gstreamer as gst;
// let pipeline = gst::parse_launch(&format!(
//     "rtspsrc location={} ! decodebin ! videoconvert ! jpegenc ! appsink",
//     rtsp_url
// ))?;
// ```
//
// Option 3: OpenCV (via opencv-rust)
// ```rust
// use opencv::videoio;
// let mut cam = videoio::VideoCapture::from_file(&rtsp_url, videoio::CAP_FFMPEG)?;
// let mut frame = opencv::core::Mat::default();
// cam.read(&mut frame)?;
// ```
