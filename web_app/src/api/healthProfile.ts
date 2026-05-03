/**
 * Health Profile API
 * API functions for managing user's health profile
 */

import { apiClient } from './client';

export interface HealthProfileData {
  health_conditions: string[];
  food_allergies: string[];
  dietary_preferences: string[];
  updated_at?: string;
}

export interface HealthProfileInput {
  health_conditions?: string[];
  food_allergies?: string[];
  dietary_preferences?: string[];
}

export const healthProfileApi = {
  /**
   * Get current user's health profile
   */
  getMyProfile: async (): Promise<HealthProfileData> => {
    const response = await apiClient.get<HealthProfileData>('/users/me/health-profile');
    return response.data;
  },

  /**
   * Update (replace) current user's health profile
   */
  updateMyProfile: async (data: HealthProfileInput): Promise<HealthProfileData> => {
    const response = await apiClient.put<HealthProfileData>('/users/me/health-profile', data);
    return response.data;
  },

  /**
   * Partially update current user's health profile
   * Only updates fields that are provided
   */
  patchMyProfile: async (data: HealthProfileInput): Promise<HealthProfileData> => {
    const response = await apiClient.patch<HealthProfileData>('/users/me/health-profile', data);
    return response.data;
  },
};
