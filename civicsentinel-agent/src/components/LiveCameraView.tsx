import React, { useEffect, useRef, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { sendNotification } from '@tauri-apps/plugin-notification';
import { useSettingsStore } from '../stores/settingsStore';

interface Detection {
  bbox: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  class_name: string;
  confidence: number;
}

interface Alert {
  zone_id: number;
  zone_name: string;
  alert_type: string;
  confidence: number;
}

interface DetectionResponse {
  camera_id: string;
  timestamp: string;
  detections: Detection[];
  alerts: Alert[];
}

interface Zone {
  id: number;
  camera_id: string;
  zone_name: string;
  coordinates: Array<{ x: number; y: number }>;
  alert_type: string;
}

interface LiveCameraViewProps {
  cameraId: string;
  cameraName: string;
  onClose: () => void;
  onEditZones?: () => void;
}

export const LiveCameraView: React.FC<LiveCameraViewProps> = ({
  cameraId,
  cameraName,
  onClose,
  onEditZones,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { backendUrl, apiKey } = useSettingsStore();
  const [detections, setDetections] = useState<Detection[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDetecting, setIsDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    detections: 0,
    alerts: 0,
    fps: 0,
  });

  // Helper: Check if point is inside polygon (for zone detection)
  const isPointInPolygon = (point: { x: number; y: number }, polygon: Array<{ x: number; y: number }>) => {
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const xi = polygon[i].x, yi = polygon[i].y;
      const xj = polygon[j].x, yj = polygon[j].y;
      const intersect = ((yi > point.y) !== (yj > point.y)) &&
        (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  };

  // Helper: Draw bounding boxes on canvas
  const drawBoundingBoxes = (
    ctx: CanvasRenderingContext2D,
    detections: Detection[],
    canvasWidth: number,
    canvasHeight: number
  ) => {
    detections.forEach((det) => {
      const { x1, y1, x2, y2 } = det.bbox;
      const width = x2 - x1;
      const height = y2 - y1;

      // Draw box
      ctx.strokeStyle = '#00ff00';
      ctx.lineWidth = 3;
      ctx.strokeRect(x1, y1, width, height);

      // Draw label background
      const label = `${det.class_name}: ${(det.confidence * 100).toFixed(0)}%`;
      ctx.font = 'bold 14px Arial';
      const metrics = ctx.measureText(label);
      const labelHeight = 22;

      ctx.fillStyle = '#00ff00';
      ctx.fillRect(x1, y1 - labelHeight, metrics.width + 12, labelHeight);

      // Draw label text
      ctx.fillStyle = '#000000';
      ctx.fillText(label, x1 + 6, y1 - 6);
    });
  };

  // Helper: Draw zones on canvas
  const drawZones = (
    ctx: CanvasRenderingContext2D,
    zones: Zone[],
    detections: Detection[]
  ) => {
    zones.forEach((zone) => {
      // Check if any detection center is inside this zone
      const isViolated = detections.some((det) => {
        const centerX = (det.bbox.x1 + det.bbox.x2) / 2;
        const centerY = (det.bbox.y1 + det.bbox.y2) / 2;
        return isPointInPolygon({ x: centerX, y: centerY }, zone.coordinates);
      });

      // Draw zone polygon
      ctx.strokeStyle = isViolated ? '#ff0000' : '#00ffff';
      ctx.fillStyle = isViolated ? 'rgba(255, 0, 0, 0.15)' : 'rgba(0, 255, 255, 0.08)';
      ctx.lineWidth = 2;

      ctx.beginPath();
      zone.coordinates.forEach((point, i) => {
        if (i === 0) {
          ctx.moveTo(point.x, point.y);
        } else {
          ctx.lineTo(point.x, point.y);
        }
      });
      ctx.closePath();
      ctx.stroke();
      ctx.fill();

      // Draw zone label
      if (zone.coordinates.length > 0) {
        const firstPoint = zone.coordinates[0];
        ctx.fillStyle = isViolated ? '#ff0000' : '#00ffff';
        ctx.font = 'bold 12px Arial';
        ctx.fillText(zone.zone_name, firstPoint.x + 5, firstPoint.y - 5);
      }
    });
  };

  // Load zones on mount
  useEffect(() => {
    const loadZones = async () => {
      if (!backendUrl || !apiKey) return;

      try {
        console.log('[LiveView] Loading zones for camera:', cameraId);
        const zonesData = await invoke<Zone[]>('get_zones', {
          cameraId,
          apiKey,
          backendUrl,
        });
        console.log('[LiveView] Loaded zones:', zonesData.length);
        setZones(zonesData);
      } catch (err) {
        console.error('[LiveView] Failed to load zones:', err);
        // Non-critical error, continue without zones
      }
    };

    loadZones();
  }, [cameraId, apiKey, backendUrl]);

  // ==========================================
  // THREE INDEPENDENT LOOPS - OPTIMIZED FOR FAST MOTION DETECTION
  // ==========================================
  useEffect(() => {
    console.log('[LiveView] Component mounted, cameraId:', cameraId);

    let mounted = true;
    let latestFrame: string | null = null;
    let previousFrame: string | null = null; // For motion detection
    let latestDetections: DetectionResponse | null = null;
    let frameCount = 0;
    let lastFpsTime = Date.now();
    let detectionQueue: string[] = []; // Queue for parallel processing
    let detecting = false;

    // Reset loading state on mount
    setIsLoading(true);

    // ==========================================
    // LOOP 1: FAST CAPTURE (2 FPS - OPTIMIZED)
    // ==========================================
    const captureLoop = setInterval(async () => {
      if (!mounted) return;

      try {
        console.log('[LiveView] Capturing frame...');

        // Capture frame - NO API call, NO blocking
        const frameBase64 = await invoke<string>('get_frame', {
          cameraId,
        });

        if (!mounted) return;

        // Cache frame for display and detection loops
        latestFrame = frameBase64;
        frameCount++;

        // Add to detection queue (max 3 frames to prevent overload)
        if (detectionQueue.length < 3) {
          detectionQueue.push(frameBase64);
        }

        console.log('[LiveView] Frame captured, size:', frameBase64.length);

        // Hide loading on FIRST successful frame
        if (frameCount === 1) {
          setIsLoading(false);
          setError(null);
        }

        // Update FPS counter
        const now = Date.now();
        if (now - lastFpsTime >= 1000) {
          setStats((prev) => ({ ...prev, fps: frameCount }));
          frameCount = 0;
          lastFpsTime = now;
        }
      } catch (err) {
        if (mounted) {
          console.error('[LiveView] Capture error:', err);
          const errorMsg = err instanceof Error ? err.message : 'Failed to capture frame';
          setError(errorMsg);
          // Don't set loading on error - keep showing last frame
        }
      }
    }, 500); // FASTER: Every 0.5 seconds (2 FPS)

    // ==========================================
    // LOOP 2: FAST AI DETECTION (2s interval + queue processing)
    // ==========================================
    const detectionLoop = setInterval(async () => {
      if (!mounted || detecting || detectionQueue.length === 0) return;

      detecting = true;
      const frame = detectionQueue.shift()!;

      // Skip detection if frame hasn't changed (no motion)
      if (frame === previousFrame) {
        console.log('[LiveView] No motion detected, skipping AI');
        detecting = false;
        return;
      }

      previousFrame = frame;

      try {
        console.log('[LiveView] Sending frame to AI backend...');
        setIsDetecting(true);

        // Send to backend for detection (optimized for faster processing)
        const detectionData = await invoke<DetectionResponse>('send_frame_to_cloud', {
          cameraId,
          frameBase64: frame,
          apiKey,
          backendUrl,
        });

        if (!mounted) return;

        console.log('[LiveView] AI detection complete:', detectionData.detections.length, 'detections');

        // Cache detection results for display loop
        latestDetections = detectionData;

        // Update state
        setDetections(detectionData.detections);
        setAlerts(detectionData.alerts);
        setStats((prev) => ({
          ...prev,
          detections: detectionData.detections.length,
          alerts: detectionData.alerts.length,
        }));

        // Handle alerts - show notifications
        if (detectionData.alerts.length > 0) {
          detectionData.alerts.forEach((alert) => {
            sendNotification({
              title: '🚨 CivicSentinel Alert',
              body: `${alert.alert_type} detected at ${cameraName} - Zone: ${alert.zone_name}`,
            });
          });
        }
      } catch (err) {
        if (mounted) {
          console.warn('[LiveView] Detection API error (non-critical):', err);
          // Detection errors don't affect video display
        }
      } finally {
        if (mounted) {
          setIsDetecting(false);
          detecting = false;
        }
      }
    }, 2000); // FASTER: Every 2 seconds (was 5 seconds)

    // ==========================================
    // LOOP 3: FAST DISPLAY RENDERING (10 FPS)
    // ==========================================
    const displayLoop = setInterval(() => {
      if (!mounted || !latestFrame) return;

      const canvas = canvasRef.current;
      if (!canvas) return;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const img = new Image();
      img.src = `data:image/jpeg;base64,${latestFrame}`;

      img.onload = () => {
        if (!mounted) return;

        // Set canvas size on first frame
        if (canvas.width === 0 || canvas.height === 0) {
          console.log('[LiveView] Setting canvas size:', img.width, 'x', img.height);
          canvas.width = img.width;
          canvas.height = img.height;
        }

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw video frame
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        // Draw zones first (behind detections)
        if (zones.length > 0) {
          drawZones(ctx, zones, latestDetections?.detections || []);
        }

        // Draw detection bounding boxes on top
        if (latestDetections?.detections && latestDetections.detections.length > 0) {
          drawBoundingBoxes(ctx, latestDetections.detections, canvas.width, canvas.height);
        }
      };

      img.onerror = (e) => {
        console.error('[LiveView] Image load error:', e);
      };
    }, 100); // 10 FPS - smooth display

    // Cleanup
    return () => {
      console.log('[LiveView] Component unmounting, cleaning up loops');
      mounted = false;
      clearInterval(captureLoop);
      clearInterval(detectionLoop);
      clearInterval(displayLoop);
    };
  }, [cameraId, cameraName, apiKey, backendUrl, zones]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-lg shadow-xl w-full max-w-6xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            <h2 className="text-xl font-semibold text-white">
              Live View: {cameraName}
            </h2>
            <div className="text-sm text-gray-400">
              {stats.fps} FPS
            </div>
            {isDetecting && (
              <div className="bg-purple-500/20 px-3 py-1 rounded">
                <span className="text-purple-400 text-sm">🤖 Detecting...</span>
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Canvas Display */}
        <div className="relative bg-black min-h-[500px]">
          {isLoading && !error && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/95">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-500 mb-6"></div>
              <p className="text-white text-xl font-semibold mb-2">Connecting to camera...</p>
              <p className="text-gray-400 text-sm">Waiting for first frame</p>
              <div className="mt-4 text-gray-500 text-xs">
                Camera: {cameraId}
              </div>
            </div>
          )}
          {error && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-red-900/90">
              <svg className="w-16 h-16 text-red-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-white text-xl font-semibold mb-2">Failed to load camera</p>
              <p className="text-red-200 text-sm mb-6 max-w-md text-center">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-3 bg-white text-red-900 rounded-lg font-semibold hover:bg-gray-100 transition"
              >
                Retry Connection
              </button>
            </div>
          )}
          <canvas
            ref={canvasRef}
            className="w-full h-auto max-h-[70vh] mx-auto"
            style={{ display: isLoading || error ? 'none' : 'block' }}
          />
        </div>

        {/* Stats Bar */}
        <div className="flex items-center justify-between p-4 border-t border-gray-700 bg-gray-800">
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-white text-sm">
                Detections: {stats.detections}
              </span>
            </div>
            {stats.alerts > 0 && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                <span className="text-red-500 text-sm font-semibold">
                  Alerts: {stats.alerts}
                </span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-sm">
                Zones: {zones.length}
              </span>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={onEditZones}
              className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 transition text-sm"
              disabled={!onEditZones}
            >
              Edit Zones
            </button>
            <button className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 transition text-sm">
              Settings
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-500 transition text-sm"
            >
              Close
            </button>
          </div>
        </div>

        {/* Active Alerts */}
        {alerts.length > 0 && (
          <div className="p-4 bg-red-900 bg-opacity-50 border-t border-red-700">
            <h3 className="text-red-400 font-semibold mb-2">Active Alerts:</h3>
            {alerts.map((alert, index) => (
              <div
                key={index}
                className="text-white text-sm py-1 flex items-center gap-2"
              >
                <span className="text-red-500">⚠️</span>
                <span>
                  {alert.alert_type} in {alert.zone_name} (confidence: {(alert.confidence * 100).toFixed(0)}%)
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
