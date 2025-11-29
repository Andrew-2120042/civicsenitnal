import React, { useState } from 'react';
import { useSettingsStore } from '../stores/settingsStore';
import { Save, Key, Globe } from 'lucide-react';

export function Settings() {
  const { backendUrl, apiKey, setBackendUrl, setApiKey } = useSettingsStore();
  const [localBackendUrl, setLocalBackendUrl] = useState(backendUrl);
  const [localApiKey, setLocalApiKey] = useState(apiKey);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setBackendUrl(localBackendUrl);
    setApiKey(localApiKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="p-6">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
          <p className="text-gray-600">
            Configure your CivicSentinel application
          </p>
        </div>

        {/* Settings Form */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="space-y-6">
            {/* Backend URL */}
            <div>
              <label
                htmlFor="backendUrl"
                className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2"
              >
                <Globe size={18} />
                Backend URL
              </label>
              <input
                id="backendUrl"
                type="text"
                value={localBackendUrl}
                onChange={(e) => setLocalBackendUrl(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="http://localhost:8000"
              />
              <p className="mt-1 text-sm text-gray-500">
                The URL of your CivicSentinel backend API
              </p>
            </div>

            {/* API Key */}
            <div>
              <label
                htmlFor="apiKey"
                className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2"
              >
                <Key size={18} />
                API Key
              </label>
              <input
                id="apiKey"
                type="password"
                value={localApiKey}
                onChange={(e) => setLocalApiKey(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Your API key"
              />
              <p className="mt-1 text-sm text-gray-500">
                Your authentication key for the backend API
              </p>
            </div>

            {/* Save Button */}
            <div className="flex items-center gap-4 pt-4">
              <button
                onClick={handleSave}
                className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg flex items-center gap-2 transition-colors"
              >
                <Save size={20} />
                Save Settings
              </button>
              {saved && (
                <span className="text-green-600 font-medium">
                  Settings saved successfully!
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            Quick Start
          </h3>
          <div className="text-sm text-blue-800 space-y-2">
            <p>
              <strong>1.</strong> Make sure your CivicSentinel backend is
              running
            </p>
            <p>
              <strong>2.</strong> Enter your backend URL (usually{' '}
              <code className="bg-blue-100 px-2 py-1 rounded">
                http://localhost:8000
              </code>
              )
            </p>
            <p>
              <strong>3.</strong> Enter your API key from the backend
            </p>
            <p>
              <strong>4.</strong> Click "Save Settings" and start monitoring!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
