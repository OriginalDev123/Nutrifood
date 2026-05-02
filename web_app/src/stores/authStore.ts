import { create } from 'zustand';
import type { User } from '../api/types';
import { authApi } from '../api/auth';
import { setOnboardingPending } from '../lib/onboardingStorage';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  /** True only while validating an existing session on app load (do not use for login/register). */
  isInitializing: boolean;
  /** True while login or register request is in flight (button spinners only). */
  isSubmitting: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  /** Đăng ký → đăng nhập → đánh dấu cần onboarding (localStorage). */
  registerThenStartOnboarding: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isInitializing: false,
  isSubmitting: false,

  login: async (email, password) => {
    set({ isSubmitting: true });
    try {
      await authApi.login({ email, password });
      const user = await authApi.me();
      set({ user, isAuthenticated: true, isSubmitting: false });
    } catch (error) {
      set({ isSubmitting: false });
      console.error("Login failed:", error); 
      throw error;
    }
  },

  register: async (email, password, fullName) => {
    set({ isSubmitting: true });
    try {
      await authApi.register({ email, password, full_name: fullName });
      set({ isSubmitting: false });
    } catch (error) {
      set({ isSubmitting: false });
      console.error("Registration failed:", error); 
      throw error;
    }
  },

  registerThenStartOnboarding: async (email, password, fullName) => {
    set({ isSubmitting: true });
    try {
      await authApi.register({ email, password, full_name: fullName });
      await authApi.login({ email, password });
      const user = await authApi.me();
      setOnboardingPending();
      set({ user, isAuthenticated: true, isSubmitting: false });
    } catch (error) {
      set({ isSubmitting: false });
      console.error("Registration failed:", error);
      throw error;
    }
  },

  logout: () => {
    authApi.logout();
    set({ user: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    set({ isInitializing: true });
    try {
      const user = await authApi.me();
      set({ user, isAuthenticated: true, isInitializing: false });
    } catch (error) {
      set({ user: null, isAuthenticated: false, isInitializing: false });
      console.error("Fetch user failed:", error); 
    }
  },
}));