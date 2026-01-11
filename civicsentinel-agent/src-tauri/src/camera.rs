use serde::{Deserialize, Serialize};
use std::net::{TcpStream, ToSocketAddrs};
use std::time::Duration;
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex as StdMutex};
use std::sync::atomic::{AtomicBool, Ordering};
use std::io::{BufReader, Read};
use std::thread;
use std::collections::VecDeque;
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
    Http(String),
    VideoFile { path: String, current_frame: usize },
}

#[derive(Debug, Clone)]
pub struct CameraHandle {
    pub source: Arc<Mutex<CameraSource>>,
    pub username: Option<String>,
    pub password: Option<String>,
    pub is_connected: bool,
    pub persistent_capture: Option<Arc<StdMutex<PersistentCapture>>>,
}

/// Scan local network for IP cameras
pub async fn scan_for_cameras() -> Result<Vec<DiscoveredCamera>, String> {
    println!("[Camera] Starting network scan...");

    let discovered_cameras = Vec::new();

    // Get local IP to determine subnet
    let local_ip = local_ip_address::local_ip()
        .map_err(|e| format!("Failed to get local IP: {}", e))?;

    println!("[Camera] Local IP: {}", local_ip);

    // Real network scanning logic would go here
    // This would:
    // 1. Parse local IP to get subnet (e.g., 192.168.1.0/24)
    // 2. Scan common camera ports (554, 8554, 8080) on each IP
    // 3. Try to connect and verify it's a camera
    // 4. Return list of discovered cameras

    // For now, return empty list - users can add cameras manually
    println!("[Camera] Network scan complete, found {} cameras", discovered_cameras.len());

    Ok(discovered_cameras)
}

/// Test if a TCP port is open and accepting connections
fn test_tcp_port(host: &str, port: u16, timeout_secs: u64) -> Result<(), String> {
    println!("[Camera] Testing TCP connection to {}:{}", host, port);

    let addr = format!("{}:{}", host, port);
    let timeout = Duration::from_secs(timeout_secs);

    match TcpStream::connect_timeout(
        &addr.to_socket_addrs()
            .map_err(|e| format!("Invalid address {}: {}", addr, e))?
            .next()
            .ok_or_else(|| format!("Could not resolve address: {}", addr))?,
        timeout
    ) {
        Ok(_) => {
            println!("[Camera] ✓ TCP port {}:{} is open and accepting connections", host, port);
            Ok(())
        },
        Err(e) => {
            println!("[Camera] ✗ TCP port {}:{} is not reachable: {}", host, port, e);
            Err(format!(
                "Port {} on {} is not reachable.\n\
                 Possible causes:\n\
                 1. RTSP server is not running on the device\n\
                 2. Firewall is blocking port {}\n\
                 3. Device is not on the network or IP is incorrect\n\n\
                 Technical details: {}",
                port, host, port, e
            ))
        }
    }
}

/// Parse RTSP URL to extract host and port
fn parse_rtsp_url(url: &str) -> Result<(String, u16), String> {
    // Expected format: rtsp://hostname:port/path or rtsp://hostname/path (default port 554)
    let without_protocol = url.strip_prefix("rtsp://")
        .ok_or_else(|| format!("Invalid RTSP URL: must start with rtsp://"))?;

    let host_port = without_protocol.split('/').next()
        .ok_or_else(|| format!("Invalid RTSP URL format"))?;

    if let Some((host, port_str)) = host_port.split_once(':') {
        let port = port_str.parse::<u16>()
            .map_err(|_| format!("Invalid port number: {}", port_str))?;
        Ok((host.to_string(), port))
    } else {
        // No port specified, use default RTSP port
        Ok((host_port.to_string(), 554))
    }
}

/// Test if a camera connection works by attempting to capture a frame
pub async fn test_camera_connection(rtsp_url: &str) -> Result<bool, String> {
    println!("[Camera] Testing connection to: {}", rtsp_url);

    // Step 1: Parse URL and test TCP port first
    let (host, port) = parse_rtsp_url(rtsp_url)?;

    println!("[Camera] Step 1/2: Testing TCP port connectivity...");
    tokio::task::spawn_blocking(move || {
        test_tcp_port(&host, port, 5)
    })
    .await
    .map_err(|e| format!("Task join error: {}", e))??;

    println!("[Camera] Step 2/2: Testing RTSP stream with FFmpeg...");

    // Step 2: Test RTSP connection with FFmpeg
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
                "-loglevel", "error",
                "-",
            ])
            .output();

        match output {
            Ok(out) => {
                let success = out.status.success();
                if success {
                    println!("[Camera] ✓ RTSP connection successful: {}", url);
                } else {
                    let error = String::from_utf8_lossy(&out.stderr);
                    println!("[Camera] ✗ RTSP connection failed: {}", error);
                    return Err(format!("RTSP stream test failed: {}", error.trim()));
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
pub async fn connect(source_url: &str, username: Option<String>, password: Option<String>) -> Result<CameraHandle, String> {
    println!("[Camera] Connecting to: {}", source_url);
    println!("[Camera] URL ends with .mp4? {}", source_url.ends_with(".mp4"));
    println!("[Camera] URL ends with .mkv? {}", source_url.ends_with(".mkv"));

    let source = if source_url.starts_with("rtsp://") {
        // RTSP stream
        println!("[Camera] Detected RTSP stream");
        CameraSource::Rtsp(source_url.to_string())
    } else if source_url.starts_with("http://") || source_url.starts_with("https://") {
        // HTTP/MJPEG stream
        println!("[Camera] Detected HTTP/MJPEG stream");
        CameraSource::Http(source_url.to_string())
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
        username,
        password,
        is_connected: true,
        persistent_capture: None,
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

/// Safe JPEG frame extractor - detects SOI (FFD8) and EOI (FFD9)
fn extract_jpeg_frames(buffer: &mut Vec<u8>) -> Vec<Vec<u8>> {
    let mut frames = Vec::new();

    loop {
        // Find SOI marker (0xFF 0xD8)
        let soi_pos = buffer.windows(2).position(|w| w == [0xFF, 0xD8]);

        if soi_pos.is_none() {
            // No SOI found, discard everything before next check
            if buffer.len() > 1 {
                buffer.drain(0..buffer.len() - 1);
            }
            break;
        }

        let soi = soi_pos.unwrap();

        // Find EOI marker (0xFF 0xD9) after SOI
        let eoi_pos = buffer[soi..].windows(2).position(|w| w == [0xFF, 0xD9]);

        if eoi_pos.is_none() {
            // SOI found but no EOI yet, keep buffer and wait for more data
            break;
        }

        let eoi = soi + eoi_pos.unwrap() + 2; // +2 to include EOI marker

        // Extract complete JPEG frame
        let frame = buffer[soi..eoi].to_vec();
        frames.push(frame);

        // Remove processed frame from buffer
        buffer.drain(0..eoi);
    }

    frames
}

/// Persistent capture process - one FFmpeg process per camera
pub struct PersistentCapture {
    process: Child,
    frame_buffer: Arc<StdMutex<VecDeque<Vec<u8>>>>,
    is_running: Arc<AtomicBool>,
    _reader_handle: Option<std::thread::JoinHandle<()>>,
}

impl std::fmt::Debug for PersistentCapture {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("PersistentCapture")
            .field("process_id", &self.process.id())
            .field("is_running", &self.is_running.load(Ordering::Relaxed))
            .field("frame_count", &self.get_frame_count())
            .finish()
    }
}

impl PersistentCapture {
    pub fn new(
        source_url: String,
        source_type: String,
        username: Option<String>,
        password: Option<String>
    ) -> Result<Self, String> {
        let ffmpeg_path = get_ffmpeg_path();

        // Build authenticated URL if credentials provided
        let auth_url = if let (Some(user), Some(pass)) = (username.as_ref(), password.as_ref()) {
            if let Some(pos) = source_url.find("://") {
                let protocol = &source_url[..pos+3];
                let rest = &source_url[pos+3..];
                format!("{}{}:{}@{}", protocol, user, pass, rest)
            } else {
                source_url.clone()
            }
        } else {
            source_url.clone()
        };

        println!("[PersistentCapture] ========================================");
        println!("[PersistentCapture] Starting FFmpeg for camera");
        println!("[PersistentCapture] FFmpeg path: {}", ffmpeg_path);
        println!("[PersistentCapture] Source URL: {}", source_url);
        println!("[PersistentCapture] Source type: {}", source_type);
        println!("[PersistentCapture] Auth URL: {}", auth_url);

        // Build FFmpeg arguments (PRODUCTION-GRADE, CPU-SAFE)
        let mut args = vec![];

        // Source-specific args
        if source_type == "rtsp" {
            args.extend(vec![
                "-rtsp_transport".to_string(),
                "tcp".to_string(),
            ]);
        } else if source_type == "file" {
            // Loop video files infinitely
            args.extend(vec![
                "-stream_loop".to_string(),
                "-1".to_string(),  // -1 means infinite loop
            ]);
        }

        // Core args (NO -re flag for RTSP!)
        args.extend(vec![
            "-i".to_string(),
            auth_url,
            "-vf".to_string(),
            "scale=960:-1".to_string(),     // CPU-safe resolution
            "-r".to_string(),
            // Video files: 15 FPS for smooth playback
            // RTSP/HTTP: 5 FPS for efficiency
            if source_type == "file" { "15".to_string() } else { "5".to_string() },
            "-f".to_string(),
            "image2pipe".to_string(),
            "-vcodec".to_string(),
            "mjpeg".to_string(),
            "-q:v".to_string(),
            "4".to_string(),                // CPU-safe quality (4, not 2)
            "-".to_string(),
        ]);

        println!("[PersistentCapture] Full command: {} {:?}", ffmpeg_path, args);
        println!("[PersistentCapture] ========================================");

        // Spawn FFmpeg with piped stdout AND stderr
        let mut child = Command::new(&ffmpeg_path)
            .args(&args)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())  // CHANGED from null to piped for debugging
            .spawn()
            .map_err(|e| format!("Failed to spawn FFmpeg: {}", e))?;

        let stdout = child.stdout.take()
            .ok_or("Failed to capture FFmpeg stdout")?;

        println!("[PersistentCapture] ✅ FFmpeg stdout captured successfully");

        // Capture stderr for debugging
        let stderr = child.stderr.take()
            .ok_or("Failed to capture FFmpeg stderr")?;

        // Spawn thread to log FFmpeg errors/info
        thread::spawn(move || {
            use std::io::BufRead;
            let reader = BufReader::new(stderr);
            for line in reader.lines() {
                if let Ok(line) = line {
                    println!("[FFmpeg stderr] {}", line);
                }
            }
        });

        // Shared state
        let frame_buffer = Arc::new(StdMutex::new(VecDeque::with_capacity(5)));
        let is_running = Arc::new(AtomicBool::new(true));

        // Clone for thread
        let buffer_clone = Arc::clone(&frame_buffer);
        let running_clone = Arc::clone(&is_running);

        // Spawn background reader thread
        let reader_handle = thread::spawn(move || {
            println!("[PersistentCapture] Reader thread started");

            let mut reader = BufReader::new(stdout);
            let mut raw_buffer = Vec::with_capacity(1024 * 1024); // 1MB buffer
            let mut read_buf = [0u8; 8192]; // 8KB read chunks

            let mut frame_count = 0;

            let mut total_bytes_read = 0;
            let mut read_count = 0;

            while running_clone.load(Ordering::Relaxed) {
                // Read from FFmpeg stdout
                match reader.read(&mut read_buf) {
                    Ok(0) => {
                        println!("[PersistentCapture] FFmpeg stream ended (total bytes: {}, reads: {})",
                            total_bytes_read, read_count);
                        break;
                    }
                    Ok(n) => {
                        read_count += 1;
                        total_bytes_read += n;

                        if read_count <= 5 || read_count % 100 == 0 {
                            println!("[PersistentCapture] Read {} bytes from FFmpeg (total: {} bytes, {} reads)",
                                n, total_bytes_read, read_count);
                        }

                        // Append to buffer
                        raw_buffer.extend_from_slice(&read_buf[0..n]);

                        if read_count <= 3 {
                            println!("[PersistentCapture] Raw buffer size: {} bytes", raw_buffer.len());
                            if raw_buffer.len() >= 10 {
                                println!("[PersistentCapture] First 10 bytes: {:02X?}", &raw_buffer[0..10]);
                            }
                        }

                        // Extract complete JPEG frames using SAFE parser
                        let frames = extract_jpeg_frames(&mut raw_buffer);

                        if read_count <= 5 || !frames.is_empty() {
                            println!("[PersistentCapture] Extracted {} frames from buffer (buffer remaining: {} bytes)",
                                frames.len(), raw_buffer.len());
                        }

                        if !frames.is_empty() {
                            let mut buffer = buffer_clone.lock().unwrap();

                            for frame in frames {
                                frame_count += 1;

                                if frame_count <= 3 {
                                    println!("[PersistentCapture] Frame {} size: {} bytes", frame_count, frame.len());
                                }

                                // Add to buffer (keep last 5 frames)
                                buffer.push_back(frame);
                                if buffer.len() > 5 {
                                    buffer.pop_front();
                                }

                                if frame_count % 50 == 0 {
                                    println!("[PersistentCapture] Captured {} frames, buffer size: {}",
                                        frame_count, buffer.len());
                                }
                            }
                        }
                    }
                    Err(e) => {
                        println!("[PersistentCapture] Read error: {} (total bytes: {}, reads: {})",
                            e, total_bytes_read, read_count);
                        break;
                    }
                }
            }

            println!("[PersistentCapture] Reader thread exiting (total frames: {})", frame_count);
        });

        println!("[PersistentCapture] Started successfully");

        Ok(Self {
            process: child,
            frame_buffer,
            is_running,
            _reader_handle: Some(reader_handle),
        })
    }

    pub fn get_frame(&self) -> Result<Vec<u8>, String> {
        let buffer = self.frame_buffer.lock().unwrap();

        // Return most recent frame
        buffer.back()
            .cloned()
            .ok_or_else(|| "No frames available yet".to_string())
    }

    pub fn get_frame_count(&self) -> usize {
        let buffer = self.frame_buffer.lock().unwrap();
        buffer.len()
    }

    pub fn stop(&mut self) -> Result<(), String> {
        println!("[PersistentCapture] Stopping...");

        // Signal thread to stop
        self.is_running.store(false, Ordering::Relaxed);

        // Kill FFmpeg process
        self.process.kill()
            .map_err(|e| format!("Failed to kill FFmpeg: {}", e))?;

        // Wait for process
        let _ = self.process.wait();

        println!("[PersistentCapture] Stopped");
        Ok(())
    }
}

/// Capture frame from RTSP stream using FFmpeg
fn capture_frame_rtsp(url: &str, username: Option<&str>, password: Option<&str>) -> Result<Vec<u8>, String> {
    // Build authenticated URL if credentials provided
    let auth_url = if let (Some(user), Some(pass)) = (username, password) {
        // Parse URL and inject credentials: rtsp://user:pass@host:port/path
        if let Some(pos) = url.find("://") {
            let protocol = &url[..pos+3];  // e.g., "rtsp://"
            let rest = &url[pos+3..];       // e.g., "host:port/path"
            let auth_url = format!("{}{}:{}@{}", protocol, user, pass, rest);
            println!("[Camera] Using RTSP authentication for user: {}", user);
            auth_url
        } else {
            url.to_string()
        }
    } else {
        url.to_string()
    };

    println!("[Camera] Capturing RTSP frame from: {}", url);

    let ffmpeg_path = get_ffmpeg_path();

    // Log the full command for debugging
    let args = vec![
        "-rtsp_transport", "tcp",  // TCP is more reliable than UDP
        "-timeout", "5000000",     // 5 second timeout (in microseconds) - CRITICAL FIX
        "-i", &auth_url,
        "-vframes", "1",           // Capture 1 frame
        "-vf", "scale=960:-1",     // Resize to 960px width
        "-f", "image2pipe",        // Output as image
        "-vcodec", "mjpeg",        // JPEG encoding
        "-q:v", "5",               // Quality (1=best, 31=worst)
        "-loglevel", "error",      // Show errors only
        "-",                       // Output to stdout
    ];

    println!("[Camera] FFmpeg command: {} {}", ffmpeg_path, args.join(" "));

    let output = Command::new(ffmpeg_path)
        .args(&args)
        .output()
        .map_err(|e| format!("Failed to execute FFmpeg: {}. Please ensure FFmpeg is installed.", e))?;

    if !output.status.success() {
        let error = String::from_utf8_lossy(&output.stderr);
        println!("[Camera] FFmpeg stderr: {}", error);

        // Provide actionable error messages
        if error.contains("Connection refused") || error.contains("Connection timed out") {
            return Err(format!(
                "Cannot connect to RTSP server at {}. Please check:\n\
                 1. IP Camera Lite app is running on your iPhone\n\
                 2. RTSP server is enabled in the app settings\n\
                 3. Both devices are on the same network ({})\n\
                 4. Port 8554 is not blocked by a firewall\n\n\
                 Technical details: {}",
                url,
                extract_ip_from_url(url).unwrap_or("unknown".to_string()),
                error.trim()
            ));
        } else if error.contains("Invalid data found") || error.contains("Server returned 404") {
            return Err(format!(
                "RTSP server found but stream path is incorrect.\n\
                 URL attempted: {}\n\
                 Common paths: /live, /stream, /h264\n\n\
                 Technical details: {}",
                url,
                error.trim()
            ));
        } else if error.contains("Immediate exit requested") || error.contains("No route to host") {
            return Err(format!(
                "Cannot reach device at {}.\n\
                 Please verify both devices are on the same network.\n\n\
                 Technical details: {}",
                extract_ip_from_url(url).unwrap_or("unknown".to_string()),
                error.trim()
            ));
        } else {
            return Err(format!("RTSP connection failed: {}", error.trim()));
        }
    }

    println!("[Camera] RTSP frame captured successfully, {} bytes", output.stdout.len());
    Ok(output.stdout)
}

/// Capture frame from HTTP/MJPEG stream using FFmpeg
fn capture_frame_http(url: &str, username: Option<&str>, password: Option<&str>) -> Result<Vec<u8>, String> {
    println!("[Camera] Capturing HTTP/MJPEG frame from: {}", url);

    let ffmpeg_path = get_ffmpeg_path();

    let mut args = vec![];

    // Add HTTP authentication headers if credentials provided
    if let (Some(user), Some(pass)) = (username, password) {
        use base64::{Engine as _, engine::general_purpose};
        let credentials = format!("{}:{}", user, pass);
        let encoded = general_purpose::STANDARD.encode(credentials.as_bytes());
        args.push("-headers".to_string());
        args.push(format!("Authorization: Basic {}\r\n", encoded));
        println!("[Camera] Using HTTP Basic Authentication");
    }

    args.extend(vec![
        "-i".to_string(), url.to_string(),
        "-vframes".to_string(), "1".to_string(),           // Capture 1 frame
        "-vf".to_string(), "scale=960:-1".to_string(),     // Resize to 960px width
        "-f".to_string(), "image2pipe".to_string(),        // Output as image
        "-vcodec".to_string(), "mjpeg".to_string(),        // JPEG encoding
        "-q:v".to_string(), "5".to_string(),               // Quality (1=best, 31=worst)
        "-".to_string(),                                   // Output to stdout
    ]);

    println!("[Camera] FFmpeg command: {} {}", ffmpeg_path, args.join(" "));

    let output = Command::new(ffmpeg_path)
        .args(&args)
        .output()
        .map_err(|e| format!("Failed to execute FFmpeg: {}. Please ensure FFmpeg is installed.", e))?;

    if !output.status.success() {
        let error = String::from_utf8_lossy(&output.stderr);
        println!("[Camera] FFmpeg stderr: {}", error);
        return Err(format!("HTTP stream capture failed: {}", error.trim()));
    }

    println!("[Camera] HTTP frame captured successfully, {} bytes", output.stdout.len());
    Ok(output.stdout)
}

/// Capture frame from HTTP with retry logic and connection health tracking
fn capture_frame_http_with_retry(url: &str, username: Option<&str>, password: Option<&str>, max_retries: u32) -> Result<Vec<u8>, String> {
    use std::time::{SystemTime, UNIX_EPOCH};

    let start_time = SystemTime::now();
    let timestamp = start_time.duration_since(UNIX_EPOCH).unwrap().as_secs();

    for attempt in 1..=max_retries {
        println!("[Camera Health] HTTP capture attempt {}/{} at timestamp {}", attempt, max_retries, timestamp);

        match capture_frame_http(url, username, password) {
            Ok(frame) => {
                let elapsed = start_time.elapsed().unwrap().as_millis();
                println!("[Camera Health] ✅ SUCCESS - HTTP frame captured in {}ms", elapsed);
                println!("[Camera Health] Connection: HEALTHY - Size: {} bytes", frame.len());
                return Ok(frame);
            },
            Err(e) => {
                let elapsed = start_time.elapsed().unwrap().as_millis();
                println!("[Camera Health] ❌ FAILURE - Attempt {}/{} failed after {}ms", attempt, max_retries, elapsed);
                println!("[Camera Health] Error: {}", e);

                // Check for common HTTP errors
                if e.contains("401") || e.contains("Unauthorized") {
                    println!("[Camera Health] ⚠️  ALERT: Authentication failed!");
                    println!("[Camera Health] Check username/password credentials");
                } else if e.contains("Connection refused") || e.contains("timeout") {
                    println!("[Camera Health] ⚠️  ALERT: HTTP server not responding!");
                    println!("[Camera Health] Possible causes:");
                    println!("[Camera Health]   1. Camera app backgrounded/closed");
                    println!("[Camera Health]   2. Network connectivity issue");
                    println!("[Camera Health]   3. Server overloaded");
                }

                if attempt < max_retries {
                    println!("[Camera Health] Retrying in 2 seconds... ({}/{} attempts remaining)", max_retries - attempt, max_retries);
                    std::thread::sleep(std::time::Duration::from_secs(2));
                } else {
                    let total_elapsed = start_time.elapsed().unwrap().as_secs();
                    println!("[Camera Health] ❌ ALL RETRIES EXHAUSTED after {} seconds", total_elapsed);
                    println!("[Camera Health] Connection: FAILED - No frames captured");
                    return Err(format!("Failed after {} retries in {}s: {}", max_retries, total_elapsed, e));
                }
            }
        }
    }

    Err("Failed to capture HTTP frame".to_string())
}

/// Extract IP address from RTSP URL for error messages
fn extract_ip_from_url(url: &str) -> Option<String> {
    url.strip_prefix("rtsp://")?
        .split(':')
        .next()
        .map(|s| s.to_string())
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RtspDiagnostics {
    pub url: String,
    pub host: String,
    pub port: u16,
    pub tcp_reachable: bool,
    pub tcp_error: Option<String>,
    pub rtsp_available: bool,
    pub rtsp_error: Option<String>,
    pub ffmpeg_path: String,
    pub ffmpeg_version: Option<String>,
    pub recommendations: Vec<String>,
}

/// Comprehensive RTSP diagnostics for troubleshooting
pub async fn diagnose_rtsp_connection(rtsp_url: &str) -> Result<RtspDiagnostics, String> {
    println!("[Camera] Running comprehensive diagnostics for: {}", rtsp_url);

    let mut diagnostics = RtspDiagnostics {
        url: rtsp_url.to_string(),
        host: String::new(),
        port: 0,
        tcp_reachable: false,
        tcp_error: None,
        rtsp_available: false,
        rtsp_error: None,
        ffmpeg_path: String::new(),
        ffmpeg_version: None,
        recommendations: Vec::new(),
    };

    // Step 1: Parse URL
    match parse_rtsp_url(rtsp_url) {
        Ok((host, port)) => {
            diagnostics.host = host.clone();
            diagnostics.port = port;
            println!("[Diagnostics] Parsed URL - Host: {}, Port: {}", host, port);
        }
        Err(e) => {
            diagnostics.recommendations.push(format!("Fix URL format: {}", e));
            return Ok(diagnostics);
        }
    }

    // Step 2: Check FFmpeg
    let ffmpeg_path = get_ffmpeg_path();
    diagnostics.ffmpeg_path = ffmpeg_path.to_string();

    let ffmpeg_check = tokio::task::spawn_blocking(move || {
        Command::new(ffmpeg_path)
            .args(&["-version"])
            .output()
    })
    .await
    .map_err(|e| format!("Task error: {}", e))?;

    match ffmpeg_check {
        Ok(output) if output.status.success() => {
            let version_output = String::from_utf8_lossy(&output.stdout);
            let version = version_output.lines().next().unwrap_or("unknown").to_string();
            diagnostics.ffmpeg_version = Some(version.clone());
            println!("[Diagnostics] FFmpeg found: {}", version);
        }
        _ => {
            diagnostics.recommendations.push(
                "Install FFmpeg: brew install ffmpeg (macOS) or https://ffmpeg.org/download.html".to_string()
            );
            return Ok(diagnostics);
        }
    }

    // Step 3: Test TCP connectivity
    let host = diagnostics.host.clone();
    let port = diagnostics.port;

    let tcp_result = tokio::task::spawn_blocking(move || {
        test_tcp_port(&host, port, 5)
    })
    .await
    .map_err(|e| format!("Task error: {}", e))?;

    match tcp_result {
        Ok(()) => {
            diagnostics.tcp_reachable = true;
            println!("[Diagnostics] TCP port is reachable");
        }
        Err(e) => {
            diagnostics.tcp_error = Some(e.clone());
            diagnostics.recommendations.push(format!(
                "Port {} is not reachable. Check: 1) RTSP server is running, 2) Correct IP address, 3) Same network",
                port
            ));
            println!("[Diagnostics] TCP port not reachable: {}", e);
            // Don't return yet - still test RTSP
        }
    }

    // Step 4: Test RTSP stream
    let url = rtsp_url.to_string();
    let rtsp_result = tokio::task::spawn_blocking(move || {
        let ffmpeg_path = get_ffmpeg_path();

        let output = Command::new(ffmpeg_path)
            .args(&[
                "-rtsp_transport", "tcp",
                "-timeout", "5000000",
                "-i", &url,
                "-vframes", "1",
                "-f", "null",
                "-loglevel", "error",
                "-",
            ])
            .output();

        match output {
            Ok(out) if out.status.success() => Ok(()),
            Ok(out) => {
                let error = String::from_utf8_lossy(&out.stderr);
                Err(error.to_string())
            }
            Err(e) => Err(format!("FFmpeg execution error: {}", e)),
        }
    })
    .await
    .map_err(|e| format!("Task error: {}", e))?;

    match rtsp_result {
        Ok(()) => {
            diagnostics.rtsp_available = true;
            diagnostics.recommendations.push("✓ RTSP connection successful! Camera is working.".to_string());
            println!("[Diagnostics] RTSP stream is working");
        }
        Err(e) => {
            diagnostics.rtsp_error = Some(e.clone());

            if e.contains("Connection refused") {
                diagnostics.recommendations.push(
                    "RTSP server found but refused connection. Check app settings for RTSP/streaming options.".to_string()
                );
            } else if e.contains("Invalid data") || e.contains("404") {
                diagnostics.recommendations.push(
                    format!("Try different stream paths: /live, /stream, /h264, or check app documentation")
                );
            } else {
                diagnostics.recommendations.push(
                    format!("RTSP error: {}. Check app documentation for correct URL format.", e)
                );
            }

            println!("[Diagnostics] RTSP stream failed: {}", e);
        }
    }

    Ok(diagnostics)
}

/// Capture frame from RTSP with retry logic and connection health tracking
fn capture_frame_rtsp_with_retry(url: &str, username: Option<&str>, password: Option<&str>, max_retries: u32) -> Result<Vec<u8>, String> {
    use std::time::{SystemTime, UNIX_EPOCH};

    let start_time = SystemTime::now();
    let timestamp = start_time.duration_since(UNIX_EPOCH).unwrap().as_secs();

    for attempt in 1..=max_retries {
        println!("[Camera Health] RTSP capture attempt {}/{} at timestamp {}", attempt, max_retries, timestamp);

        match capture_frame_rtsp(url, username, password) {
            Ok(frame) => {
                let elapsed = start_time.elapsed().unwrap().as_millis();
                println!("[Camera Health] ✅ SUCCESS - Frame captured in {}ms", elapsed);
                println!("[Camera Health] Connection: HEALTHY - Size: {} bytes", frame.len());
                return Ok(frame);
            },
            Err(e) => {
                let elapsed = start_time.elapsed().unwrap().as_millis();
                println!("[Camera Health] ❌ FAILURE - Attempt {}/{} failed after {}ms", attempt, max_retries, elapsed);
                println!("[Camera Health] Error: {}", e);

                // Check if it's a connection refused error
                if e.contains("Connection refused") {
                    println!("[Camera Health] ⚠️  ALERT: RTSP server not responding!");
                    println!("[Camera Health] Possible causes:");
                    println!("[Camera Health]   1. iPhone camera app went to background/sleep");
                    println!("[Camera Health]   2. iPhone screen locked (power saving)");
                    println!("[Camera Health]   3. RTSP server hit connection limit");
                    println!("[Camera Health]   4. Network connectivity issue");
                }

                if attempt < max_retries {
                    println!("[Camera Health] Retrying in 2 seconds... ({}/{} attempts remaining)", max_retries - attempt, max_retries);
                    std::thread::sleep(std::time::Duration::from_secs(2));
                } else {
                    let total_elapsed = start_time.elapsed().unwrap().as_secs();
                    println!("[Camera Health] ❌ ALL RETRIES EXHAUSTED after {} seconds", total_elapsed);
                    println!("[Camera Health] Connection: FAILED - No frames captured");
                    return Err(format!("Failed after {} retries in {}s: {}", max_retries, total_elapsed, e));
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

    // Clone credentials for use in blocking tasks
    let username = handle.username.clone();
    let password = handle.password.clone();

    match &mut *source {
        CameraSource::Rtsp(url) => {
            // Capture from real RTSP stream with retry logic
            let url = url.clone();
            // Run blocking FFmpeg call in a blocking task to avoid blocking async runtime
            tokio::task::spawn_blocking(move || {
                capture_frame_rtsp_with_retry(
                    &url,
                    username.as_deref(),
                    password.as_deref(),
                    3
                )
            })
            .await
            .map_err(|e| format!("Task join error: {}", e))?
        }
        CameraSource::Http(url) => {
            // Capture from HTTP/MJPEG stream with retry logic
            let url = url.clone();
            // Run blocking FFmpeg call in a blocking task to avoid blocking async runtime
            tokio::task::spawn_blocking(move || {
                capture_frame_http_with_retry(
                    &url,
                    username.as_deref(),
                    password.as_deref(),
                    3
                )
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
