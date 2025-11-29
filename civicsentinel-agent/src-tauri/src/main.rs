// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod camera;
mod api;

use tauri::{Manager, State, Window};
use tauri::menu::{Menu, MenuItem};
use tauri::tray::{TrayIconBuilder, TrayIconEvent};
use std::sync::{Arc, Mutex};
use std::collections::HashMap;

// Shared state for camera connections
type CameraMap = Arc<Mutex<HashMap<String, camera::CameraHandle>>>;

// Cache for latest frames and detection results
#[derive(Clone)]
struct CachedData {
    frame: String, // base64 encoded
    detections: api::DetectionResponse,
    timestamp: std::time::SystemTime,
}

type FrameCache = Arc<Mutex<HashMap<String, CachedData>>>;

#[derive(Clone, serde::Serialize)]
struct Payload {
    message: String,
}

// Tauri Commands

#[tauri::command]
async fn scan_network() -> Result<Vec<camera::DiscoveredCamera>, String> {
    println!("[Rust] Starting network scan...");
    camera::scan_for_cameras().await
}

#[tauri::command]
async fn test_camera(rtsp_url: String) -> Result<bool, String> {
    println!("[Rust] Testing camera: {}", rtsp_url);
    camera::test_camera_connection(&rtsp_url).await
}

#[tauri::command]
async fn connect_camera(
    camera_id: String,
    rtsp_url: String,
    cameras: State<'_, CameraMap>,
) -> Result<(), String> {
    println!("[Rust] Connecting camera: {}", camera_id);

    let handle = camera::connect(&rtsp_url).await?;

    cameras.lock()
        .map_err(|e| format!("Lock error: {}", e))?
        .insert(camera_id, handle);

    Ok(())
}

#[tauri::command]
async fn get_frame(
    camera_id: String,
    cameras: State<'_, CameraMap>,
) -> Result<String, String> {
    // Clone the handle while holding the lock, then drop the lock before await
    let handle = {
        let cameras_lock = cameras.lock()
            .map_err(|e| format!("Lock error: {}", e))?;

        cameras_lock.get(&camera_id)
            .ok_or_else(|| format!("Camera {} not found", camera_id))?
            .clone()
    }; // Lock is dropped here

    let frame_bytes = camera::capture_frame(&handle).await?;

    // Convert to base64 for frontend
    use base64::{Engine as _, engine::general_purpose};
    Ok(general_purpose::STANDARD.encode(&frame_bytes))
}

#[tauri::command]
async fn disconnect_camera(
    camera_id: String,
    cameras: State<'_, CameraMap>,
) -> Result<(), String> {
    println!("[Rust] Disconnecting camera: {}", camera_id);

    cameras.lock()
        .map_err(|e| format!("Lock error: {}", e))?
        .remove(&camera_id);

    Ok(())
}

#[tauri::command]
async fn send_frame_to_cloud(
    camera_id: String,
    frame_base64: String,
    api_key: String,
    backend_url: String,
    cache: State<'_, FrameCache>,
) -> Result<api::DetectionResponse, String> {
    println!("[Rust] Sending frame to cloud for camera: {}", camera_id);

    use base64::{Engine as _, engine::general_purpose};
    let frame_bytes = general_purpose::STANDARD.decode(&frame_base64)
        .map_err(|e| format!("Base64 decode error: {}", e))?;

    let response = api::send_detection_request(
        &backend_url,
        &camera_id,
        &frame_bytes,
        &api_key,
    ).await?;

    // Cache the frame and detection results
    cache.lock()
        .map_err(|e| format!("Cache lock error: {}", e))?
        .insert(camera_id.clone(), CachedData {
            frame: frame_base64,
            detections: response.clone(),
            timestamp: std::time::SystemTime::now(),
        });

    Ok(response)
}

#[tauri::command]
async fn get_latest_frame(
    camera_id: String,
    cache: State<'_, FrameCache>,
) -> Result<String, String> {
    println!("[Rust] get_latest_frame called for camera: {}", camera_id);

    let result = cache.lock()
        .map_err(|e| format!("Cache lock error: {}", e))?
        .get(&camera_id)
        .map(|cached| cached.frame.clone())
        .ok_or_else(|| format!("No cached frame for camera: {}", camera_id));

    match &result {
        Ok(frame) => println!("[Rust] Returning cached frame, length: {}", frame.len()),
        Err(e) => println!("[Rust] Error getting frame: {}", e),
    }

    result
}

#[tauri::command]
async fn get_latest_detections(
    camera_id: String,
    cache: State<'_, FrameCache>,
) -> Result<api::DetectionResponse, String> {
    println!("[Rust] get_latest_detections called for camera: {}", camera_id);

    let result = cache.lock()
        .map_err(|e| format!("Cache lock error: {}", e))?
        .get(&camera_id)
        .map(|cached| cached.detections.clone())
        .ok_or_else(|| format!("No cached detections for camera: {}", camera_id));

    match &result {
        Ok(detections) => println!("[Rust] Returning cached detections: {} detections, {} alerts",
                                    detections.detections.len(), detections.alerts.len()),
        Err(e) => println!("[Rust] Error getting detections: {}", e),
    }

    result
}

#[tauri::command]
async fn create_zone(
    camera_id: String,
    zone_name: String,
    coordinates: Vec<[f64; 2]>,
    alert_type: String,
    api_key: String,
    backend_url: String,
) -> Result<api::ZoneResponse, String> {
    println!("[Rust] Creating zone for camera: {}", camera_id);

    api::create_zone(
        &backend_url,
        &camera_id,
        &zone_name,
        &coordinates,
        &alert_type,
        &api_key,
    ).await
}

#[tauri::command]
async fn get_zones(
    camera_id: String,
    api_key: String,
    backend_url: String,
) -> Result<Vec<api::ZoneResponse>, String> {
    api::get_zones(&backend_url, &camera_id, &api_key).await
}

#[tauri::command]
async fn delete_zone(
    camera_id: String,
    zone_id: i64,
    api_key: String,
    backend_url: String,
) -> Result<(), String> {
    println!("[Rust] Deleting zone {} for camera: {}", zone_id, camera_id);
    api::delete_zone(&backend_url, &camera_id, zone_id, &api_key).await
}

#[tauri::command]
async fn show_notification(title: String, body: String, window: Window) {
    use tauri_plugin_notification::NotificationExt;

    let _ = window.app_handle()
        .notification()
        .builder()
        .title(title)
        .body(body)
        .show();
}

#[tauri::command]
async fn get_alerts(
    api_key: String,
    backend_url: String,
    camera_id: Option<String>,
    page: i64,
    page_size: i64,
) -> Result<api::AlertListResponse, String> {
    println!("[Rust] Fetching alerts from backend");

    api::get_alerts(
        &backend_url,
        &api_key,
        camera_id.as_deref(),
        page,
        page_size,
    ).await
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(CameraMap::default())
        .manage(FrameCache::default())
        .setup(|app| {
            // Create system tray
            let toggle = MenuItem::with_id(app, "toggle", "Monitoring: ON", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;

            let menu = Menu::with_items(app, &[&toggle, &quit])?;

            let _tray = TrayIconBuilder::new()
                .menu(&menu)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "toggle" => {
                        println!("Toggle monitoring");
                        // TODO: Implement monitoring toggle
                    }
                    "quit" => {
                        println!("Quit from tray");
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click { .. } = event {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            scan_network,
            test_camera,
            connect_camera,
            get_frame,
            disconnect_camera,
            send_frame_to_cloud,
            get_latest_frame,
            get_latest_detections,
            create_zone,
            get_zones,
            delete_zone,
            show_notification,
            get_alerts,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
