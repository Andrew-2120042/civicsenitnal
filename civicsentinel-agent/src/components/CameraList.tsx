import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';
import { Camera, Video, Play, Pause, Settings as SettingsIcon, Edit, Plus, FileVideo, Eye } from 'lucide-react';
import { useCameraStore } from '../stores/cameraStore';
import { useSettingsStore } from '../stores/settingsStore';
import { ZoneEditor } from './ZoneEditor';
import { LiveCameraView } from './LiveCameraView';

export function CameraList() {
  const { cameras, updateCamera, toggleMonitoring, addCamera } = useCameraStore();
  const { backendUrl, apiKey } = useSettingsStore();
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [editingZone, setEditingZone] = useState<string | null>(null);
  const [liveViewCamera, setLiveViewCamera] = useState<{ id: string; name: string } | null>(null);

  const handleAddVideoFile = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'Video Files',
          extensions: ['mp4', 'avi', 'mov', 'mkv']
        }]
      });

      if (selected) {
        const filePath = selected as string;
        const fileName = filePath.split('/').pop() || 'video';
        const id = `video_${fileName.replace(/[^a-zA-Z0-9]/g, '_')}`;

        addCamera({
          id,
          name: fileName,
          rtspUrl: filePath,  // Store file path as rtspUrl
          status: 'disconnected',
          isMonitoring: false,
        });
      }
    } catch (error) {
      console.error('Failed to select video file:', error);
      alert('Failed to select video file: ' + error);
    }
  };

  // Auto-fetch frames for monitoring cameras
  useEffect(() => {
    const interval = setInterval(() => {
      cameras.forEach(async (cam) => {
        if (cam.isMonitoring && cam.status === 'connected') {
          try {
            // Get frame from Rust
            const frameBase64: string = await invoke('get_frame', {
              cameraId: cam.id,
            });

            // Send to cloud for detection
            const result = await invoke('send_frame_to_cloud', {
              cameraId: cam.id,
              frameBase64,
              apiKey,
              backendUrl,
            });

            console.log('Detection result:', result);
            console.log('Alerts in result:', (result as any).alerts);
            console.log('Number of alerts:', (result as any).alerts?.length);

            // Update camera frame
            updateCamera(cam.id, { lastFrame: frameBase64 });

            // If alerts, show notification
            if ((result as any).alerts?.length > 0) {
              console.log('Showing notification for alert:', (result as any).alerts[0]);
              await invoke('show_notification', {
                title: '🚨 CivicSentinel Alert',
                body: `${(result as any).alerts[0].alert_type} detected at ${cam.name}`,
              });
            } else {
              console.log('No alerts to show notification for');
            }
          } catch (error) {
            console.error('Failed to process frame:', error);
          }
        }
      });
    }, 3000); // Every 3 seconds

    return () => clearInterval(interval);
  }, [cameras, apiKey, backendUrl]);

  const handleConnect = async (cameraId: string) => {
    const camera = cameras.find((c) => c.id === cameraId);
    if (!camera) return;

    try {
      await invoke('connect_camera', {
        cameraId,
        rtspUrl: camera.rtspUrl,
      });

      updateCamera(cameraId, { status: 'connected' });
    } catch (error) {
      console.error('Failed to connect camera:', error);
      updateCamera(cameraId, { status: 'error' });
    }
  };

  const handleEditZone = async (cameraId: string) => {
    const camera = cameras.find((c) => c.id === cameraId);
    if (!camera) return;

    // If no frame available, capture one first
    if (!camera.lastFrame) {
      try {
        const frameBase64: string = await invoke('get_frame', {
          cameraId,
        });
        updateCamera(cameraId, { lastFrame: frameBase64 });
      } catch (error) {
        console.error('Failed to capture frame:', error);
        alert('Failed to capture frame: ' + error);
        return;
      }
    }

    setEditingZone(cameraId);
  };

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Camera Monitoring
            </h1>
            <p className="text-gray-600">
              Manage and monitor your connected cameras
            </p>
          </div>
          <button
            onClick={handleAddVideoFile}
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg flex items-center gap-2 transition-colors shadow-md"
          >
            <FileVideo size={20} />
            Add Video File
          </button>
        </div>

        {/* Camera Grid */}
        {cameras.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Camera className="text-gray-400 mx-auto mb-4" size={48} />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              No Cameras Connected
            </h2>
            <p className="text-gray-600 mb-6">
              Add cameras from the discovery screen to get started
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cameras.map((camera) => (
              <div
                key={camera.id}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
              >
                {/* Camera Preview */}
                <div className="bg-gray-900 aspect-video flex items-center justify-center relative">
                  {camera.lastFrame ? (
                    <img
                      src={`data:image/jpeg;base64,${camera.lastFrame}`}
                      alt={camera.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <Video className="text-gray-600" size={48} />
                  )}

                  {/* Status Badge */}
                  <div className="absolute top-3 left-3">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        camera.status === 'connected'
                          ? 'bg-green-500 text-white'
                          : camera.status === 'disconnected'
                          ? 'bg-gray-500 text-white'
                          : 'bg-red-500 text-white'
                      }`}
                    >
                      {camera.status}
                    </span>
                  </div>

                  {/* Monitoring Badge */}
                  {camera.isMonitoring && (
                    <div className="absolute top-3 right-3">
                      <span className="px-2 py-1 rounded bg-purple-500 text-white text-xs font-medium flex items-center gap-1">
                        <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                        LIVE
                      </span>
                    </div>
                  )}
                </div>

                {/* Camera Info */}
                <div className="p-4">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    {camera.name}
                  </h3>
                  <p className="text-sm text-gray-500 truncate mb-4">
                    {camera.rtspUrl}
                  </p>

                  {/* Actions */}
                  <div className="flex gap-2">
                    {camera.status === 'connected' ? (
                      <>
                        <button
                          onClick={() => toggleMonitoring(camera.id)}
                          className={`flex-1 font-medium py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                            camera.isMonitoring
                              ? 'bg-purple-600 hover:bg-purple-700 text-white'
                              : 'border border-gray-300 hover:bg-gray-50 text-gray-700'
                          }`}
                        >
                          {camera.isMonitoring ? (
                            <>
                              <Pause size={16} />
                              Pause
                            </>
                          ) : (
                            <>
                              <Play size={16} />
                              Monitor
                            </>
                          )}
                        </button>

                        <button
                          onClick={() => setLiveViewCamera({ id: camera.id, name: camera.name })}
                          className="border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-2 px-3 rounded-lg flex items-center gap-2 transition-colors"
                          title="View Live"
                        >
                          <Eye size={16} />
                        </button>

                        <button
                          onClick={() => handleEditZone(camera.id)}
                          className="border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-2 px-3 rounded-lg flex items-center gap-2 transition-colors"
                          title="Edit Zones"
                        >
                          <Edit size={16} />
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => handleConnect(camera.id)}
                        className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-3 rounded-lg transition-colors"
                      >
                        Connect
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Zone Editor Modal */}
      {editingZone && (
        <ZoneEditor
          cameraId={editingZone}
          frameBase64={cameras.find((c) => c.id === editingZone)?.lastFrame}
          onClose={() => setEditingZone(null)}
        />
      )}

      {/* Live Camera View Modal */}
      {liveViewCamera && (
        <LiveCameraView
          cameraId={liveViewCamera.id}
          cameraName={liveViewCamera.name}
          onClose={() => setLiveViewCamera(null)}
          onEditZones={() => {
            setLiveViewCamera(null);
            handleEditZone(liveViewCamera.id);
          }}
        />
      )}
    </div>
  );
}
