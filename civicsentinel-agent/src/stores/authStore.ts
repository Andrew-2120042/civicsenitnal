import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '../lib/types';

interface AuthStore {
  apiKey: string;
  user: User | null;
  isAuthenticated: boolean;
  setApiKey: (key: string) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      apiKey: '',
      user: null,
      isAuthenticated: false,

      setApiKey: (key) =>
        set({
          apiKey: key,
          isAuthenticated: key.length > 0,
        }),

      setUser: (user) =>
        set({
          user,
        }),

      logout: () =>
        set({
          apiKey: '',
          user: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
