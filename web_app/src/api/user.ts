import { apiClient } from './client';
import type { UserProfile, UserGoal, WeightLog } from './types';

export const userApi = {
  getProfile: async (): Promise<UserProfile> => {
    const response = await apiClient.get('/users/me/profile');
    return response.data;
  },

  updateProfile: async (data: Partial<UserProfile>): Promise<UserProfile> => {
    const response = await apiClient.patch('/users/me/profile', data);
    return response.data;
  },

  createGoal: async (data: Partial<UserGoal>): Promise<UserGoal> => {
    const response = await apiClient.post('/users/me/goals', data);
    return response.data;
  },

  getActiveGoal: async (): Promise<UserGoal> => {
    const response = await apiClient.get('/users/me/goals/active');
    return response.data;
  },

  getGoals: async (): Promise<UserGoal[]> => {
    const response = await apiClient.get('/users/me/goals');
    return response.data;
  },

  logWeight: async (data: { weight_kg: number; measured_date: string; notes?: string }): Promise<WeightLog> => {
    const response = await apiClient.post('/food-logs/weight', data);
    return response.data;
  },

  getWeightHistory: async (limit: number = 30): Promise<WeightLog[]> => {
    const response = await apiClient.get('/food-logs/weight', { params: { limit } });
    return response.data;
  },
  
  getLatestWeight: async (): Promise<WeightLog> => {
    const response = await apiClient.get('/food-logs/weight/latest');
    return response.data;
  }
};