import React, { useRef, useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Camera as LucideCamera, Save, X, Edit2, Trash2, Plus } from 'lucide-react';
import { Zone } from '../lib/types';
import { useSettingsStore } from '../stores/settingsStore';

interface Point {
  x: number;
  y: number;
}

interface ZoneEditorProps {
  cameraId: string;
  frameBase64?: string;
  onClose: () => void;
}

export function ZoneEditor({ cameraId, frameBase64, onClose }: ZoneEditorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [points, setPoints] = useState<Point[]>([]);
  const [isDrawing, setIsDrawing] = useState(true);
  const [zoneName, setZoneName] = useState('');
  const [alertType, setAlertType] = useState('intrusion');
  const [zones, setZones] = useState<Zone[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedZone, setSelectedZone] = useState<Zone | null>(null);
  const [draggingPointIndex, setDraggingPointIndex] = useState<number | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);

  const { backendUrl, apiKey } = useSettingsStore();

  // Load existing zones
  useEffect(() => {
    loadZones();
  }, [cameraId]);

  // Draw on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const drawAllZones = () => {
      // Draw existing zones
      zones.forEach((zone) => {
        if (zone.camera_id === cameraId) {
          const isSelected = selectedZone?.id === zone.id;
          const isDimmed = selectedZone !== null && !isSelected;
          drawZone(ctx, zone.coordinates, zone.name, isSelected, isDimmed);
        }
      });
    };

    // Draw background image
    if (frameBase64) {
      const img = new Image();
      img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        drawPoints(ctx);
        drawAllZones();
      };
      img.src = `data:image/jpeg;base64,${frameBase64}`;
    } else {
      // Draw placeholder
      ctx.fillStyle = '#1a1a1a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#666';
      ctx.font = '20px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('No frame available', canvas.width / 2, canvas.height / 2);
      drawPoints(ctx);
      drawAllZones();
    }
  }, [frameBase64, points, zones, selectedZone]);

  const drawPoints = (ctx: CanvasRenderingContext2D) => {
    if (points.length === 0) return;

    // Draw lines
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    if (!isDrawing && points.length > 2) {
      ctx.closePath();
    }
    ctx.stroke();

    // Draw semi-transparent fill if closed
    if (!isDrawing && points.length > 2) {
      ctx.fillStyle = 'rgba(239, 68, 68, 0.1)';
      ctx.fill();
    }

    // Draw points
    points.forEach((point, index) => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#ef4444';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw point number
      ctx.fillStyle = '#fff';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText((index + 1).toString(), point.x, point.y - 10);
    });
  };

  const drawZone = (
    ctx: CanvasRenderingContext2D,
    coordinates: [number, number][],
    name: string,
    isSelected: boolean,
    isDimmed: boolean = false
  ) => {
    if (coordinates.length < 3) return;

    // Draw polygon
    if (isSelected) {
      // Selected zone: bright blue, thick line
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 4;
    } else if (isDimmed) {
      // Dimmed zones: very faint
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.3)';
      ctx.lineWidth = 1;
    } else {
      // Normal zones: green
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2;
    }

    ctx.beginPath();
    ctx.moveTo(coordinates[0][0], coordinates[0][1]);
    for (let i = 1; i < coordinates.length; i++) {
      ctx.lineTo(coordinates[i][0], coordinates[i][1]);
    }
    ctx.closePath();
    ctx.stroke();

    // Fill
    if (isSelected) {
      ctx.fillStyle = 'rgba(59, 130, 246, 0.3)'; // Brighter fill for selected
    } else if (isDimmed) {
      ctx.fillStyle = 'rgba(16, 185, 129, 0.05)'; // Very faint for dimmed
    } else {
      ctx.fillStyle = 'rgba(16, 185, 129, 0.1)';
    }
    ctx.fill();

    // Draw label
    const centerX = coordinates.reduce((sum, c) => sum + c[0], 0) / coordinates.length;
    const centerY = coordinates.reduce((sum, c) => sum + c[1], 0) / coordinates.length;

    if (!isDimmed) {
      // Only show label for non-dimmed zones
      const bgColor = isSelected ? '#3b82f6' : '#10b981';
      const labelWidth = isSelected ? 140 : 120;
      const labelHeight = isSelected ? 35 : 30;

      ctx.fillStyle = bgColor;
      ctx.fillRect(centerX - labelWidth/2, centerY - labelHeight/2, labelWidth, labelHeight);
      ctx.fillStyle = '#fff';
      ctx.font = isSelected ? 'bold 16px Arial' : 'bold 14px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(name, centerX, centerY + 5);
    }
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = ((e.clientX - rect.left) * canvas.width) / rect.width;
    const y = ((e.clientY - rect.top) * canvas.height) / rect.height;

    setPoints([...points, { x, y }]);
  };

  const handleCanvasDoubleClick = () => {
    if (points.length >= 3) {
      setIsDrawing(false);
    }
  };

  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDrawing || !isEditMode) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = ((e.clientX - rect.left) * canvas.width) / rect.width;
    const y = ((e.clientY - rect.top) * canvas.height) / rect.height;

    // Check if clicking near a point
    const pointIndex = points.findIndex(
      (p) => Math.sqrt((p.x - x) ** 2 + (p.y - y) ** 2) < 10
    );

    if (pointIndex !== -1) {
      setDraggingPointIndex(pointIndex);
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (draggingPointIndex === null) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = ((e.clientX - rect.left) * canvas.width) / rect.width;
    const y = ((e.clientY - rect.top) * canvas.height) / rect.height;

    const newPoints = [...points];
    newPoints[draggingPointIndex] = { x, y };
    setPoints(newPoints);
  };

  const handleCanvasMouseUp = () => {
    setDraggingPointIndex(null);
  };

  const handleSaveZone = async () => {
    if (points.length < 3) {
      setError('Please draw a polygon with at least 3 points');
      return;
    }

    if (!zoneName) {
      setError('Please enter a zone name');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const coordinates: [number, number][] = points.map((p) => [p.x, p.y]);

      // If editing, delete the old zone first
      if (isEditMode && selectedZone) {
        await invoke('delete_zone', {
          cameraId,
          zoneId: selectedZone.id,
          apiKey,
          backendUrl,
        });
      }

      // Create the new/updated zone
      const zone: Zone = await invoke('create_zone', {
        cameraId,
        zoneName,
        coordinates,
        alertType,
        apiKey,
        backendUrl,
      });

      console.log(isEditMode ? 'Zone updated:' : 'Zone created:', zone);

      // Reset
      setPoints([]);
      setZoneName('');
      setIsDrawing(true);
      setIsEditMode(false);
      setSelectedZone(null);
      await loadZones();
    } catch (err) {
      setError(err as string);
      console.error(isEditMode ? 'Failed to update zone:' : 'Failed to create zone:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadZones = async () => {
    try {
      const zonesData: Zone[] = await invoke('get_zones', {
        cameraId,
        apiKey,
        backendUrl,
      });
      setZones(zonesData);
    } catch (err) {
      console.error('Failed to load zones:', err);
    }
  };

  const handleReset = () => {
    setPoints([]);
    setIsDrawing(true);
    setZoneName('');
    setError('');
    setSelectedZone(null);
    setIsEditMode(false);
  };

  const handleEditZone = (zone: Zone) => {
    setSelectedZone(zone);
    setPoints(zone.coordinates.map(([x, y]) => ({ x, y })));
    setZoneName(zone.name);
    setAlertType(zone.alert_type || zone.alertType || 'intrusion');
    setIsDrawing(false);
    setIsEditMode(true);
  };

  const handleAddNewZone = () => {
    setPoints([]);
    setZoneName('');
    setAlertType('intrusion');
    setIsDrawing(true);
    setSelectedZone(null);
    setIsEditMode(false);
    setError('');
  };

  const handleDeleteZone = async (zoneId: number) => {
    if (!confirm('Are you sure you want to delete this zone?')) {
      return;
    }

    setLoading(true);
    try {
      await invoke('delete_zone', {
        cameraId,
        zoneId,
        apiKey,
        backendUrl,
      });

      console.log('Zone deleted:', zoneId);
      await loadZones();

      // Clear selection if deleted zone was selected
      if (selectedZone?.id === zoneId) {
        setSelectedZone(null);
        handleReset();
      }
    } catch (err) {
      setError(err as string);
      console.error('Failed to delete zone:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <LucideCamera size={24} />
            <h2 className="text-xl font-bold">Zone Editor - Camera {cameraId}</h2>
          </div>
          <button
            onClick={onClose}
            className="hover:bg-white/20 rounded p-2 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Canvas Area */}
          <div className="flex-1 bg-gray-900 flex items-center justify-center p-4 overflow-auto">
            <canvas
              ref={canvasRef}
              width={640}
              height={480}
              onClick={handleCanvasClick}
              onDoubleClick={handleCanvasDoubleClick}
              onMouseDown={handleCanvasMouseDown}
              onMouseMove={handleCanvasMouseMove}
              onMouseUp={handleCanvasMouseUp}
              onMouseLeave={handleCanvasMouseUp}
              className={`border-2 border-gray-700 max-w-full h-auto ${
                isDrawing ? 'cursor-crosshair' : isEditMode ? 'cursor-move' : 'cursor-default'
              }`}
              style={{ imageRendering: 'crisp-edges' }}
            />
          </div>

          {/* Control Panel */}
          <div className="w-80 bg-gray-50 p-6 flex flex-col gap-4 overflow-y-auto">
            {/* Drawing Instructions */}
            {isDrawing && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">How to Draw:</h3>
                <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                  <li>Click on canvas to add points</li>
                  <li>Minimum 3 points required</li>
                  <li>Double-click to close polygon</li>
                  <li>Fill in zone details below</li>
                </ol>
                <p className="text-xs text-blue-600 mt-2">
                  Points: {points.length}
                </p>
              </div>
            )}

            {/* Edit Mode Instructions */}
            {isEditMode && !isDrawing && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-semibold text-green-900 mb-2">Edit Mode:</h3>
                <ol className="text-sm text-green-800 space-y-1 list-decimal list-inside">
                  <li>Drag the points to adjust zone</li>
                  <li>Update zone name or alert type</li>
                  <li>Click Save to update zone</li>
                  <li>Click Reset to start over</li>
                </ol>
                <p className="text-xs text-green-600 mt-2">
                  Editing: {selectedZone?.name}
                </p>
              </div>
            )}

            {/* Zone Configuration */}
            {!isDrawing && points.length >= 3 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Zone Name *
                  </label>
                  <input
                    type="text"
                    value={zoneName}
                    onChange={(e) => setZoneName(e.target.value)}
                    placeholder="e.g., Restricted Area"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Alert Type
                  </label>
                  <select
                    value={alertType}
                    onChange={(e) => setAlertType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="intrusion">Intrusion</option>
                    <option value="loitering">Loitering</option>
                    <option value="counting">Counting</option>
                  </select>
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded-lg text-sm">
                    {error}
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={handleSaveZone}
                    disabled={loading}
                    className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
                  >
                    <Save size={18} />
                    {loading ? (isEditMode ? 'Updating...' : 'Saving...') : (isEditMode ? 'Update Zone' : 'Save Zone')}
                  </button>

                  <button
                    onClick={handleReset}
                    className="px-4 py-2 border border-gray-300 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>
            )}

            {/* Start Drawing Button */}
            {!isDrawing && points.length < 3 && (
              <button
                onClick={() => setIsDrawing(true)}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Edit2 size={18} />
                Start Drawing Zone
              </button>
            )}

            {/* Reset Drawing */}
            {isDrawing && points.length > 0 && (
              <button
                onClick={handleReset}
                className="w-full border border-gray-300 hover:bg-gray-100 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors"
              >
                Reset Drawing
              </button>
            )}

            {/* Existing Zones */}
            <div className="border-t border-gray-200 pt-4 mt-4">
              <h3 className="font-semibold text-gray-900 mb-3">Existing Zones ({zones.length})</h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {zones.map((zone) => (
                  <div
                    key={zone.id}
                    className={`border rounded-lg p-3 ${
                      selectedZone?.id === zone.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    } transition-colors`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1 cursor-pointer" onClick={() => {
                        setSelectedZone(zone);
                        setPoints([]);
                        setIsDrawing(false);
                        setIsEditMode(false);
                      }}>
                        <p className="font-medium text-gray-900">{zone.name}</p>
                        <p className="text-xs text-gray-500 capitalize">{zone.alert_type}</p>
                      </div>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          zone.active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {zone.active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEditZone(zone)}
                        className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
                        disabled={loading}
                      >
                        <Edit2 size={14} />
                        Edit
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteZone(zone.id);
                        }}
                        className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
                        disabled={loading}
                      >
                        <Trash2 size={14} />
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
