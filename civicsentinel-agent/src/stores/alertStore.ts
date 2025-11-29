import { create } from 'zustand';
import { Alert } from '../lib/types';

interface AlertStore {
  alerts: Alert[];
  addAlert: (alert: Alert) => void;
  clearAlerts: () => void;
  getRecentAlerts: (limit: number) => Alert[];
}

export const useAlertStore = create<AlertStore>((set, get) => ({
  alerts: [],

  addAlert: (alert) =>
    set((state) => ({
      alerts: [alert, ...state.alerts].slice(0, 100), // Keep last 100
    })),

  clearAlerts: () => set({ alerts: [] }),

  getRecentAlerts: (limit) => get().alerts.slice(0, limit),
}));
