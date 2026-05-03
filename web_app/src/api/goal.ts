import { apiClient } from './client';
import type { UserGoal } from './types';

export interface CreateGoalData {
  goal_type: 'weight_loss' | 'weight_gain' | 'maintain' | 'healthy_lifestyle';
  target_weight_kg?: number;
  target_date?: string;
  daily_calorie_target?: number;
  protein_target_g?: number;
  carbs_target_g?: number;
  fat_target_g?: number;
  activity_level?: 'sedentary' | 'lightly_active' | 'moderately_active' | 'very_active' | 'extra_active';
  current_weight_kg?: number;
  health_conditions?: string[];
  food_allergies?: string[];
  dietary_preferences?: string[];
}

export interface UpdateGoalData {
  target_weight_kg?: number;
  target_date?: string;
  daily_calorie_target?: number;
  protein_target_g?: number;
  carbs_target_g?: number;
  fat_target_g?: number;
  health_conditions?: string[];
  food_allergies?: string[];
  dietary_preferences?: string[];
}

export const goalApi = {
  /**
   * Create a new goal (automatically deactivates existing active goal)
   */
  create: async (data: CreateGoalData): Promise<UserGoal> => {
    const response = await apiClient.post('/users/me/goals', data);
    return response.data;
  },

  /**
   * Get all goals for current user
   */
  getAll: async (activeOnly: boolean = false): Promise<UserGoal[]> => {
    const response = await apiClient.get('/users/me/goals', {
      params: { active_only: activeOnly },
    });
    return response.data;
  },

  /**
   * Get active goal
   */
  getActive: async (): Promise<UserGoal> => {
    const response = await apiClient.get('/users/me/goals/active');
    return response.data;
  },

  /**
   * Update a specific goal (partial update)
   */
  update: async (goalId: string, data: UpdateGoalData): Promise<UserGoal> => {
    const response = await apiClient.patch(`/users/me/goals/${goalId}`, data);
    return response.data;
  },

  /**
   * Deactivate a goal (soft delete)
   */
  deactivate: async (goalId: string): Promise<void> => {
    await apiClient.delete(`/users/me/goals/${goalId}`);
  },

  /**
   * Full update a goal (replace all fields)
   */
  replace: async (goalId: string, data: CreateGoalData): Promise<UserGoal> => {
    const response = await apiClient.put(`/users/me/goals/${goalId}`, data);
    return response.data;
  },
};
