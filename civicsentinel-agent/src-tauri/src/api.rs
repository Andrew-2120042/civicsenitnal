use serde::{Deserialize, Serialize};
use reqwest::multipart;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoundingBox {
    pub x1: f64,
    pub y1: f64,
    pub x2: f64,
    pub y2: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Detection {
    #[serde(rename = "class")]
    pub class_name: String,
    pub confidence: f64,
    pub bbox: BoundingBox,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ZoneAlert {
    pub zone_id: i64,
    pub zone_name: String,
    pub alert_type: String,
    pub confidence: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetectionResponse {
    pub camera_id: String,
    pub timestamp: String,
    pub detections: Vec<Detection>,
    pub alerts: Vec<ZoneAlert>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ZoneResponse {
    pub id: i64,
    pub camera_id: String,
    pub name: String,
    pub coordinates: Vec<[f64; 2]>,
    pub alert_type: String,
    pub active: bool,
    pub active_hours: Option<String>,
    pub created_at: String,
}

#[derive(Debug, Serialize)]
struct ZoneCreateRequest {
    name: String,
    coordinates: Vec<[f64; 2]>,
    alert_type: String,
    active: bool,
}

/// Send frame to cloud API for detection
pub async fn send_detection_request(
    backend_url: &str,
    camera_id: &str,
    frame_bytes: &[u8],
    api_key: &str,
) -> Result<DetectionResponse, String> {
    let client = reqwest::Client::new();

    let url = format!("{}/api/v1/detect", backend_url);

    // Create multipart form
    let part = multipart::Part::bytes(frame_bytes.to_vec())
        .file_name("frame.jpg")
        .mime_str("image/jpeg")
        .map_err(|e| format!("Failed to create multipart: {}", e))?;

    let form = multipart::Form::new()
        .part("image", part)
        .text("camera_id", camera_id.to_string());

    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .multipart(form)
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        return Err(format!("API error {}: {}", status, text));
    }

    let detection: DetectionResponse = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(detection)
}

/// Create a new zone for a camera
pub async fn create_zone(
    backend_url: &str,
    camera_id: &str,
    zone_name: &str,
    coordinates: &[[f64; 2]],
    alert_type: &str,
    api_key: &str,
) -> Result<ZoneResponse, String> {
    let client = reqwest::Client::new();

    let url = format!("{}/api/v1/cameras/{}/zones", backend_url, camera_id);

    let request_body = ZoneCreateRequest {
        name: zone_name.to_string(),
        coordinates: coordinates.to_vec(),
        alert_type: alert_type.to_string(),
        active: true,
    };

    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Content-Type", "application/json")
        .json(&request_body)
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        return Err(format!("API error {}: {}", status, text));
    }

    let zone: ZoneResponse = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(zone)
}

/// Get all zones for a camera
pub async fn get_zones(
    backend_url: &str,
    camera_id: &str,
    api_key: &str,
) -> Result<Vec<ZoneResponse>, String> {
    let client = reqwest::Client::new();

    let url = format!("{}/api/v1/cameras/{}/zones", backend_url, camera_id);

    let response = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        return Err(format!("API error {}: {}", status, text));
    }

    let zones: Vec<ZoneResponse> = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(zones)
}

/// Delete a zone
pub async fn delete_zone(
    backend_url: &str,
    camera_id: &str,
    zone_id: i64,
    api_key: &str,
) -> Result<(), String> {
    let client = reqwest::Client::new();

    let url = format!("{}/api/v1/cameras/{}/zones/{}", backend_url, camera_id, zone_id);

    let response = client
        .delete(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        return Err(format!("API error {}: {}", status, text));
    }

    Ok(())
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlertResponse {
    pub id: i64,
    pub camera_id: String,
    pub zone_id: i64,
    pub detection_type: String,
    pub confidence: f64,
    pub bbox: Option<BoundingBox>,
    pub image_url: Option<String>,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlertListResponse {
    pub alerts: Vec<AlertResponse>,
    pub total: i64,
    pub page: i64,
    pub page_size: i64,
}

/// Get alerts from the cloud API
pub async fn get_alerts(
    backend_url: &str,
    api_key: &str,
    camera_id: Option<&str>,
    page: i64,
    page_size: i64,
) -> Result<AlertListResponse, String> {
    let client = reqwest::Client::new();

    let mut url = format!("{}/api/v1/alerts?page={}&page_size={}", backend_url, page, page_size);

    if let Some(cam_id) = camera_id {
        url = format!("{}&camera_id={}", url, cam_id);
    }

    let response = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        return Err(format!("API error {}: {}", status, text));
    }

    let alerts: AlertListResponse = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(alerts)
}
