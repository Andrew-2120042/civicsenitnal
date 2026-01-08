import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Settings } from '../lib/types';

interface SettingsStore extends Settings {
  updateSettings: (settings: Partial<Settings>) => void;
  setBackendUrl: (url: string) => void;
  setApiKey: (key: string) => void;
  resetSettings: () => void;
}

const defaultSettings: Settings = {
  backendUrl: 'http://localhost:8000',
  apiKey: 'test_api_key_123',
  enableNotifications: true,
  enableSound: true,
  confidenceThreshold: 0.5,
};

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      ...defaultSettings,

      updateSettings: (settings) =>
        set((state) => ({
          ...state,
          ...settings,
        })),

      setBackendUrl: (url) =>
        set({ backendUrl: url }),

      setApiKey: (key) =>
        set({ apiKey: key }),

      resetSettings: () => set(defaultSettings),
    }),
    {
      name: 'settings-storage',
    }
  )
);
