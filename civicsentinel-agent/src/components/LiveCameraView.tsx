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
  const [isLoading, setIsLoading] = useState(true);
  const [loadingStatus, setLoadingStatus] = useState('Initializing...');
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    detections: 0,
    alerts: 0,
  });

  // Draw detection overlays on canvas
  const drawDetections = (
    ctx: CanvasRenderingContext2D,
    detections: Detection[]
  ) => {
    // Draw bounding boxes
    detections.forEach((det) => {
      const width = det.bbox.x2 - det.bbox.x1;
      const height = det.bbox.y2 - det.bbox.y1;

      // Draw box
      ctx.strokeStyle = '#00ff00';
      ctx.lineWidth = 2;
      ctx.strokeRect(det.bbox.x1, det.bbox.y1, width, height);

      // Draw label background
      const label = `${det.class_name}: ${det.confidence.toFixed(2)}`;
      ctx.font = '12px Arial';
      const metrics = ctx.measureText(label);
      const labelHeight = 18;

      ctx.fillStyle = '#00ff00';
      ctx.fillRect(
        det.bbox.x1,
        det.bbox.y1 - labelHeight,
        metrics.width + 8,
        labelHeight
      );

      // Draw label text
      ctx.fillStyle = '#000000';
      ctx.fillText(label, det.bbox.x1 + 4, det.bbox.y1 - 5);
    });
  };

  // Parallel frame processing - OPTIMIZED for smooth playback
  useEffect(() => {
    console.log('[LiveView] Component mounted, cameraId:', cameraId, 'backendUrl:', backendUrl);

    let mounted = true;
    let latestFrameBase64: string | null = null;
    let latestDetectionData: Detection[] = [];
    let displayInterval: NodeJS.Timeout;
    let captureInterval: NodeJS.Timeout;

    // Fast display loop (10 FPS) - just displays cached frame
    const displayFrame = () => {
      if (!mounted || !latestFrameBase64) {
        return;
      }

      const canvas = canvasRef.current;
      if (!canvas) {
        console.warn('[LiveView] Canvas ref not available');
        return;
      }

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.warn('[LiveView] Canvas context not available');
        return;
      }

      const img = new Image();
      img.src = `data:image/jpeg;base64,${latestFrameBase64}`;

      img.onload = () => {
        if (!mounted) return;

        // Set canvas size to match image (only on first frame)
        if (canvas.width === 0 || canvas.height === 0) {
          console.log('[LiveView] Setting canvas size:', img.width, 'x', img.height);
          canvas.width = img.width;
          canvas.height = img.height;
        }

        // Draw image
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        // Draw detection overlays
        if (latestDetectionData.length > 0) {
          drawDetections(ctx, latestDetectionData);
        }
      };

      img.onerror = (e) => {
        console.error('[LiveView] Image load error:', e);
      };
    };

    // Slow capture + API loop (2 FPS)
    const captureAndProcess = async () => {
      try {
        console.log('[LiveView] Starting frame capture for camera:', cameraId);
        setLoadingStatus('Capturing frame...');

        // Step 1: Capture frame from camera with timeout
        const frameBase64 = await Promise.race([
          invoke<string>('get_frame', { cameraId }),
          new Promise<string>((_, reject) =>
            setTimeout(() => reject(new Error('Frame capture timeout (10s)')), 10000)
          ),
        ]);

        console.log('[LiveView] Frame captured, size:', frameBase64?.length);

        if (!mounted) return;

        // Cache frame for display loop
        latestFrameBase64 = frameBase64;

        console.log('[LiveView] Frame cached, starting display');
        setLoadingStatus('Processing with AI...');
        setIsLoading(false); // Show frame immediately, even before AI processing
        setError(null);

        // Step 2: Send to API in background (don't block display)
        invoke<DetectionResponse>('send_frame_to_cloud', {
          cameraId,
          frameBase64,
          apiKey,
          backendUrl,
        }).then((detectionData) => {
          if (!mounted) return;

          console.log('[LiveView] AI processing complete, detections:', detectionData.detections.length);

          // Update cached detections
          latestDetectionData = detectionData.detections;

          // Update state
          setDetections(detectionData.detections);
          setAlerts(detectionData.alerts);
          setStats({
            detections: detectionData.detections.length,
            alerts: detectionData.alerts.length,
          });

          // Handle alerts - show notifications
          if (detectionData.alerts.length > 0) {
            detectionData.alerts.forEach((alert) => {
              sendNotification({
                title: '🚨 CivicSentinel Alert',
                body: `${alert.alert_type} detected at ${cameraName} - Zone: ${alert.zone_name}`,
              });
            });
          }
        }).catch((err) => {
          if (mounted) {
            console.error('[LiveView] API error:', err);
          }
        });
      } catch (err) {
        if (mounted) {
          console.error('[LiveView] Capture error:', err);
          const errorMsg = err instanceof Error ? err.message : 'Failed to capture frame';
          setError(errorMsg);
          setIsLoading(false);
        }
      }
    };

    // Initial capture
    captureAndProcess();

    // Start display loop at 10 FPS (100ms interval)
    displayInterval = setInterval(displayFrame, 100);

    // Start capture loop at 2 FPS (500ms interval)
    captureInterval = setInterval(captureAndProcess, 500);

    return () => {
      console.log('[LiveView] Component unmounting, cleaning up intervals');
      mounted = false;
      if (displayInterval) clearInterval(displayInterval);
      if (captureInterval) clearInterval(captureInterval);
    };
  }, [cameraId, cameraName, apiKey, backendUrl]);

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
              <p className="text-white text-xl font-semibold mb-2">{loadingStatus}</p>
              <p className="text-gray-400 text-sm">This may take 5-10 seconds</p>
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
              <p className="text-white text-xl font-semibold mb-2">❌ Failed to load camera</p>
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
            style={{ display: isLoading && !error ? 'none' : 'block' }}
          />
        </div>

        {/* Stats Bar */}
        <div className="flex items-center justify-between p-4 border-t border-gray-700 bg-gray-800">
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
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
                  {alert.alert_type} in {alert.zone_name} (confidence: {alert.confidence.toFixed(2)})
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
