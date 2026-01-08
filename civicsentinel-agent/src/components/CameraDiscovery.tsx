import React, { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';
import { Search, Wifi, Check, X, Video, Radio } from 'lucide-react';
import { DiscoveredCamera } from '../lib/types';
import { useCameraStore } from '../stores/cameraStore';

interface CameraDiscoveryProps {
  onComplete: () => void;
}

export function CameraDiscovery({ onComplete }: CameraDiscoveryProps) {
  const [isScanning, setIsScanning] = useState(false);
  const [discoveredCameras, setDiscoveredCameras] = useState<DiscoveredCamera[]>([]);
  const [selectedCameras, setSelectedCameras] = useState<Set<string>>(new Set());
  const [cameraNames, setCameraNames] = useState<Record<string, string>>({});
  const [showManualDialog, setShowManualDialog] = useState(false);
  const [manualUrl, setManualUrl] = useState('');
  const [manualName, setManualName] = useState('');
  const [manualUsername, setManualUsername] = useState('');
  const [manualPassword, setManualPassword] = useState('');
  const { addCamera } = useCameraStore();

  const handleScan = async () => {
    setIsScanning(true);
    try {
      const cameras: DiscoveredCamera[] = await invoke('scan_network');
      setDiscoveredCameras(cameras);
      console.log('Discovered cameras:', cameras);
    } catch (error) {
      console.error('Failed to scan network:', error);
      alert('Failed to scan network: ' + error);
    } finally {
      setIsScanning(false);
    }
  };

  const toggleCamera = (ip: string) => {
    const newSelected = new Set(selectedCameras);
    if (newSelected.has(ip)) {
      newSelected.delete(ip);
    } else {
      newSelected.add(ip);
    }
    setSelectedCameras(newSelected);
  };

  const handleSelectVideoFile = async () => {
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

        onComplete();
      }
    } catch (error) {
      console.error('Failed to select video file:', error);
      alert('Failed to select video file: ' + error);
    }
  };

  const handleAddManualCamera = () => {
    if (!manualUrl || !manualName) {
      alert('Please enter both camera name and stream URL');
      return;
    }

    if (!manualUrl.startsWith('rtsp://') && !manualUrl.startsWith('http://') && !manualUrl.startsWith('https://')) {
      alert('Stream URL must start with rtsp://, http://, or https://');
      return;
    }

    const id = `cam_${manualName.replace(/[^a-zA-Z0-9]/g, '_')}`;

    addCamera({
      id,
      name: manualName,
      rtspUrl: manualUrl,
      username: manualUsername || undefined,
      password: manualPassword || undefined,
      status: 'disconnected',
      isMonitoring: false,
    });

    setShowManualDialog(false);
    setManualUrl('');
    setManualName('');
    setManualUsername('');
    setManualPassword('');
    onComplete();
  };

  const handleContinue = async () => {
    // Add selected cameras to store
    selectedCameras.forEach((ip) => {
      const camera = discoveredCameras.find((c) => c.ip === ip);
      if (camera) {
        const id = `cam_${ip.replace(/\./g, '_')}`;
        addCamera({
          id,
          name: cameraNames[ip] || `Camera ${ip}`,
          rtspUrl: camera.rtsp_url,
          status: 'disconnected',
          isMonitoring: false,
        });
      }
    });

    onComplete();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Wifi className="text-purple-600" size={32} />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Find Your Cameras
            </h1>
            <p className="text-gray-600">
              We'll scan your local network for IP cameras
            </p>
          </div>

          {/* Scan Button */}
          {discoveredCameras.length === 0 && (
            <div className="text-center">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
                <button
                  onClick={handleScan}
                  disabled={isScanning}
                  className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-semibold py-4 px-8 rounded-lg flex items-center justify-center gap-3 transition-colors"
                >
                  <Search size={20} />
                  {isScanning ? 'Scanning...' : 'Scan Network'}
                </button>

                <button
                  onClick={() => setShowManualDialog(true)}
                  disabled={isScanning}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-4 px-8 rounded-lg flex items-center justify-center gap-3 transition-colors"
                >
                  <Radio size={20} />
                  Add Network Camera
                </button>

                <button
                  onClick={handleSelectVideoFile}
                  disabled={isScanning}
                  className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white font-semibold py-4 px-8 rounded-lg flex items-center justify-center gap-3 transition-colors"
                >
                  <Video size={20} />
                  Use Video File
                </button>
              </div>

              {isScanning && (
                <div className="mt-6">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
                  <p className="text-gray-600 mt-4">
                    This may take 10-30 seconds...
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Discovered Cameras List */}
          {discoveredCameras.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Found {discoveredCameras.length} Camera(s)
              </h2>

              <div className="space-y-3 mb-6">
                {discoveredCameras.map((camera, index) => {
                  const isSelected = selectedCameras.has(camera.ip);
                  return (
                    <div
                      key={`${index}-${camera.ip}`}
                      className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                        isSelected
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => toggleCamera(camera.ip)}
                    >
                      <div className="flex items-center gap-4">
                        <div
                          className={`w-6 h-6 rounded border-2 flex items-center justify-center ${
                            isSelected
                              ? 'bg-purple-600 border-purple-600'
                              : 'border-gray-300'
                          }`}
                        >
                          {isSelected && <Check className="text-white" size={16} />}
                        </div>

                        <div className="flex-1">
                          <p className="font-medium text-gray-900">
                            {camera.ip}
                          </p>
                          <p className="text-sm text-gray-500 truncate">
                            {camera.rtsp_url}
                          </p>
                        </div>

                        {isSelected && (
                          <input
                            type="text"
                            placeholder="Camera name..."
                            value={cameraNames[camera.ip] || ''}
                            onChange={(e) => {
                              e.stopPropagation();
                              setCameraNames({
                                ...cameraNames,
                                [camera.ip]: e.target.value,
                              });
                            }}
                            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            onClick={(e) => e.stopPropagation()}
                          />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={handleScan}
                  className="flex-1 border-2 border-gray-300 hover:border-gray-400 text-gray-700 font-medium py-3 px-4 rounded-lg transition-colors"
                >
                  Scan Again
                </button>

                <button
                  onClick={handleContinue}
                  disabled={selectedCameras.size === 0}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
                >
                  Continue ({selectedCameras.size} selected)
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Manual Camera Dialog */}
      {showManualDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Add Network Camera</h2>
            <p className="text-sm text-gray-600 mb-4">Supports RTSP and HTTP/MJPEG streams</p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Camera Name
                </label>
                <input
                  type="text"
                  value={manualName}
                  onChange={(e) => setManualName(e.target.value)}
                  placeholder="e.g., Front Door Camera"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stream URL
                </label>
                <input
                  type="text"
                  value={manualUrl}
                  onChange={(e) => setManualUrl(e.target.value)}
                  placeholder="rtsp://192.168.1.100:554/stream or http://192.168.1.100:8080/video"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
                <p className="mt-1 text-xs text-gray-500">
                  RTSP: rtsp://host:port/path or HTTP: http://host:port/path
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username (optional)
                </label>
                <input
                  type="text"
                  value={manualUsername}
                  onChange={(e) => setManualUsername(e.target.value)}
                  placeholder="admin"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password (optional)
                </label>
                <input
                  type="password"
                  value={manualPassword}
                  onChange={(e) => setManualPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Common default: admin/admin (check your camera manual)
                </p>
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => setShowManualDialog(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddManualCamera}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Add Camera
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
