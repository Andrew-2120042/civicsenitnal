import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Camera } from '../lib/types';

interface CameraStore {
  cameras: Camera[];
  addCamera: (camera: Camera) => void;
  removeCamera: (id: string) => void;
  updateCamera: (id: string, updates: Partial<Camera>) => void;
  getCameraById: (id: string) => Camera | undefined;
  toggleMonitoring: (id: string) => void;
}

export const useCameraStore = create<CameraStore>()(
  persist(
    (set, get) => ({
      cameras: [],

      addCamera: (camera) =>
        set((state) => ({
          cameras: [...state.cameras, camera],
        })),

      removeCamera: (id) =>
        set((state) => ({
          cameras: state.cameras.filter((cam) => cam.id !== id),
        })),

      updateCamera: (id, updates) =>
        set((state) => ({
          cameras: state.cameras.map((cam) =>
            cam.id === id ? { ...cam, ...updates } : cam
          ),
        })),

      getCameraById: (id) => get().cameras.find((cam) => cam.id === id),

      toggleMonitoring: (id) =>
        set((state) => ({
          cameras: state.cameras.map((cam) =>
            cam.id === id ? { ...cam, isMonitoring: !cam.isMonitoring } : cam
          ),
        })),
    }),
    {
      name: 'camera-storage',
    }
  )
);
