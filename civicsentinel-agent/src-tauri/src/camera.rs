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

/// Test if a camera connection works by attempting to capture a frame
pub async fn test_camera_connection(rtsp_url: &str) -> Result<bool, String> {
    println!("[Camera] Testing connection to: {}", rtsp_url);

    // Test RTSP connection by attempting to capture a frame
    let url = rtsp_url.to_string();
    let result = tokio::task::spawn_blocking(move || {
        let ffmpeg_path = get_ffmpeg_path();

        println!("[Camera] Testing RTSP with ffmpeg: {}", url);

        let output = Command::new(ffmpeg_path)
            .args(&[
                "-rtsp_transport", "tcp",
                "-timeout", "5000000",  // 5 second timeout (in microseconds)
                "-i", &url,
                "-vframes", "1",
                "-f", "null",
                "-",
            ])
            .output();

        match output {
            Ok(out) => {
                let success = out.status.success();
                if success {
                    println!("[Camera] ✓ RTSP connection successful: {}", url);
                } else {
                    println!("[Camera] ✗ RTSP connection failed: {}", url);
                }
                Ok(success)
            },
            Err(e) => {
                println!("[Camera] ✗ FFmpeg error: {}", e);
                Err(format!("FFmpeg error: {}", e))
            }
        }
    })
    .await
    .map_err(|e| format!("Task join error: {}", e))??;

    Ok(result)
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

/// Helper function to get ffmpeg path
fn get_ffmpeg_path() -> &'static str {
    if std::path::Path::new("/opt/homebrew/bin/ffmpeg").exists() {
        "/opt/homebrew/bin/ffmpeg"
    } else if std::path::Path::new("/usr/local/bin/ffmpeg").exists() {
        "/usr/local/bin/ffmpeg"
    } else {
        "ffmpeg" // Fallback to PATH
    }
}

/// Capture frame from RTSP stream using FFmpeg
fn capture_frame_rtsp(url: &str) -> Result<Vec<u8>, String> {
    println!("[Camera] Capturing RTSP frame from: {}", url);

    let ffmpeg_path = get_ffmpeg_path();

    let output = Command::new(ffmpeg_path)
        .args(&[
            "-rtsp_transport", "tcp",  // TCP is more reliable than UDP
            "-i", url,
            "-vframes", "1",           // Capture 1 frame
            "-vf", "scale=960:-1",     // Resize to 960px width
            "-f", "image2pipe",        // Output as image
            "-vcodec", "mjpeg",        // JPEG encoding
            "-q:v", "5",               // Quality (1=best, 31=worst)
            "-",                       // Output to stdout
        ])
        .output()
        .map_err(|e| format!("Failed to capture RTSP frame: {}", e))?;

    if !output.status.success() {
        let error = String::from_utf8_lossy(&output.stderr);
        return Err(format!("FFmpeg error: {}", error));
    }

    println!("[Camera] RTSP frame captured successfully, {} bytes", output.stdout.len());
    Ok(output.stdout)
}

/// Capture frame from RTSP with retry logic
fn capture_frame_rtsp_with_retry(url: &str, max_retries: u32) -> Result<Vec<u8>, String> {
    for attempt in 1..=max_retries {
        println!("[Camera] RTSP capture attempt {}/{}", attempt, max_retries);

        match capture_frame_rtsp(url) {
            Ok(frame) => {
                println!("[Camera] RTSP frame captured successfully");
                return Ok(frame);
            },
            Err(e) => {
                if attempt < max_retries {
                    println!("[Camera] RTSP capture failed, retrying in 2s: {}", e);
                    std::thread::sleep(std::time::Duration::from_secs(2));
                } else {
                    println!("[Camera] RTSP capture failed after {} attempts", max_retries);
                    return Err(format!("Failed after {} retries: {}", max_retries, e));
                }
            }
        }
    }

    Err("Failed to capture RTSP frame".to_string())
}

/// Capture a single frame from camera or video file
pub async fn capture_frame(handle: &CameraHandle) -> Result<Vec<u8>, String> {
    if !handle.is_connected {
        return Err("Camera not connected".to_string());
    }

    let mut source = handle.source.lock().await;

    match &mut *source {
        CameraSource::Rtsp(url) => {
            // Capture from real RTSP stream with retry logic
            let url = url.clone();
            // Run blocking FFmpeg call in a blocking task to avoid blocking async runtime
            tokio::task::spawn_blocking(move || {
                capture_frame_rtsp_with_retry(&url, 3)
            })
            .await
            .map_err(|e| format!("Task join error: {}", e))?
        }
        CameraSource::VideoFile { path, current_frame } => {
            // Extract frame using ffmpeg
            let frame_num = *current_frame;
            *current_frame += 1;  // Increment for next call

            let path_clone = path.clone();

            // Run blocking FFmpeg call in a blocking task
            let result = tokio::task::spawn_blocking(move || {
                let ffmpeg_path = get_ffmpeg_path();

                let output = Command::new(ffmpeg_path)
                    .args(&[
                        "-i", &path_clone,
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
                    return capture_frame_at_position(&path_clone, 0);
                }

                Ok(output.stdout)
            })
            .await
            .map_err(|e| format!("Task join error: {}", e))?;

            // Reset frame counter if we looped
            if result.is_ok() && frame_num > 0 {
                // Check if we looped by seeing if result came from position 0
                // If so, reset counter
                match result {
                    Ok(ref bytes) if bytes.len() > 0 => {
                        // Successfully got frame
                    }
                    _ => {
                        *current_frame = 1; // Reset and we just got frame 0
                    }
                }
            }

            result
        }
    }
}

/// Helper function to capture frame at specific position
fn capture_frame_at_position(video_path: &str, frame_num: usize) -> Result<Vec<u8>, String> {
    let ffmpeg_path = get_ffmpeg_path();

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
