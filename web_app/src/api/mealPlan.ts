import { apiClient } from './client';
import type {
  MealPlan,
  MealPlanWithItems,
  MealPlanDay,
  ShoppingListResponse,
  MealPlanAnalysis,
} from './extended';
import type { HealthProfileData } from './healthProfile';

export interface GenerateMealPlanParams {
  plan_name: string;
  days?: number;
  categories?: string;
  tags?: string;
  max_cook_time?: number;
  health_profile?: HealthProfileData;
}

export interface RegenerateDayParams {
  plan_id: string;
  target_date: string;
}

export const mealPlanApi = {
  /**
   * Generate a new meal plan with AI-like algorithm
   * Supports health_profile for personalized meal planning
   */
  generateMealPlan: async (params: GenerateMealPlanParams): Promise<MealPlanWithItems> => {
    const response = await apiClient.post<MealPlanWithItems>('/meal-plans/generate', {
      plan_name: params.plan_name,
      days: params.days || 7,
      categories: params.categories,
      tags: params.tags,
      max_cook_time: params.max_cook_time,
      health_profile: params.health_profile,
    });
    return response.data;
  },

  /**
   * Get all meal plans for current user
   */
  getMyPlans: async (activeOnly: boolean = false): Promise<MealPlan[]> => {
    const response = await apiClient.get('/meal-plans', {
      params: { active_only: activeOnly },
    });
    return response.data;
  },

  /**
   * Get detailed meal plan with items
   */
  getPlanDetail: async (planId: string): Promise<MealPlanWithItems> => {
    const response = await apiClient.get(`/meal-plans/${planId}`);
    return response.data;
  },

  /**
   * Get shopping list for a meal plan
   */
  getShoppingList: async (planId: string): Promise<ShoppingListResponse> => {
    const response = await apiClient.get(`/meal-plans/${planId}/shopping-list`);
    return response.data;
  },

  /**
   * Get nutrition analysis for a meal plan
   */
  analyzeMealPlan: async (planId: string): Promise<MealPlanAnalysis> => {
    const response = await apiClient.get(`/meal-plans/${planId}/analysis`);
    return response.data;
  },

  /**
   * Regenerate a specific day in the meal plan
   */
  regenerateDay: async (planId: string, targetDate: string): Promise<MealPlanDay['items']> => {
    const response = await apiClient.post(`/meal-plans/${planId}/regenerate-day`, null, {
      params: { target_date: targetDate },
    });
    return response.data;
  },

  /**
   * Delete a meal plan
   */
  deletePlan: async (planId: string): Promise<void> => {
    await apiClient.delete(`/meal-plans/${planId}`);
  },

  /**
   * Update meal plan name
   */
  updatePlanName: async (planId: string, planName: string): Promise<MealPlan> => {
    const response = await apiClient.patch(`/meal-plans/${planId}`, { plan_name: planName });
    return response.data;
  },

  /**
   * Archive a meal plan
   */
  archivePlan: async (planId: string): Promise<MealPlan> => {
    const response = await apiClient.patch(`/meal-plans/${planId}`, { status: 'archived' });
    return response.data;
  },
};
