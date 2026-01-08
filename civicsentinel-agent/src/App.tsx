import React, { useState } from 'react';
import { CameraDiscovery } from './components/CameraDiscovery';
import { CameraList } from './components/CameraList';
import { Alerts } from './components/Alerts';
import { Settings } from './components/Settings';
import { useCameraStore } from './stores/cameraStore';
import { Camera, AlertTriangle, Settings as SettingsIcon } from 'lucide-react';

type View = 'cameras' | 'alerts' | 'settings';

function App() {
  const { cameras } = useCameraStore();
  const [showDiscovery, setShowDiscovery] = useState(cameras.length === 0);
  const [currentView, setCurrentView] = useState<View>('cameras');

  if (showDiscovery) {
    return <CameraDiscovery onComplete={() => setShowDiscovery(false)} />;
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center h-16">
            <div className="text-xl font-bold text-purple-600 mr-8">
              CivicSentinel
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentView('cameras')}
                className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors ${
                  currentView === 'cameras'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Camera size={20} />
                Cameras
              </button>
              <button
                onClick={() => setCurrentView('alerts')}
                className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors ${
                  currentView === 'alerts'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <AlertTriangle size={20} />
                Alerts
              </button>
              <button
                onClick={() => setCurrentView('settings')}
                className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors ${
                  currentView === 'settings'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <SettingsIcon size={20} />
                Settings
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="flex-1 overflow-auto bg-gray-50">
        {currentView === 'cameras' && <CameraList />}
        {currentView === 'alerts' && <Alerts />}
        {currentView === 'settings' && <Settings />}
      </div>
    </div>
  );
}

export default App;
