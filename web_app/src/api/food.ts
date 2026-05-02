import { apiClient } from './client';
import type { Food, FoodLog, FoodSearchResponse, DailySummary } from './types';

export interface FoodPortionPreset {
  preset_id: string;
  size_label: string;
  display_name_vi: string;
  display_name_en: string | null;
  unit_type: string;
  unit_display_vi: string;
  grams: number;
  is_default: boolean;
  sort_order: number;
}

export interface FoodLogHistoryResponse {
  start_date: string;
  end_date: string;
  total_logs: number;
  logs_by_date: Record<string, FoodLog[]>;
}

export const foodApi = {
  getFoods: async (params?: { skip?: number; limit?: number; category?: string; verified_only?: boolean }): Promise<FoodSearchResponse> => {
    const response = await apiClient.get('/foods', { params });
    return response.data;
  },

  getFoodDetail: async (foodId: string): Promise<Food> => {
    const response = await apiClient.get(`/foods/${foodId}`);
    return response.data;
  },

  searchFoods: async (query: string, params?: { skip?: number; limit?: number }): Promise<FoodSearchResponse> => {
    const response = await apiClient.get('/foods/search', {
      params: { q: query, ...params },
    });
    return response.data;
  },

  getCategories: async (): Promise<string[]> => {
    const response = await apiClient.get('/foods/categories');
    return response.data;
  },

  getByBarcode: async (barcode: string): Promise<Food> => {
    const response = await apiClient.get(`/foods/barcode/${barcode}`);
    return response.data;
  },

  getPortions: async (foodId: string): Promise<FoodPortionPreset[]> => {
    const response = await apiClient.get(`/foods/${foodId}/portions`);
    return response.data;
  },

  logMeal: async (data: {
    food_id: string;
    serving_id?: string;
    meal_type: string;
    meal_date: string;
    quantity?: number;
    serving_size_g?: number;
    meal_time?: string;
    notes?: string;
  }): Promise<FoodLog> => {
    const response = await apiClient.post('/food-logs/', data);
    return response.data;
  },

  getDailySummary: async (date: string): Promise<DailySummary> => {
    const response = await apiClient.get('/food-logs/summary', {
      params: { meal_date: date },
    });
    return response.data;
  },

  getFoodLogs: async (date: string): Promise<FoodLog[]> => {
    const response = await apiClient.get('/food-logs/', {
      params: { meal_date: date },
    });
    return response.data;
  },

  getFoodLogHistory: async (
    startDate: string,
    endDate: string,
    mealType?: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  ): Promise<FoodLogHistoryResponse> => {
    const response = await apiClient.get('/food-logs/history', {
      params: { start_date: startDate, end_date: endDate, meal_type: mealType },
    });
    return response.data;
  },

  updateFoodLog: async (
    logId: string,
    data: Partial<{
      quantity: number;
      meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
      meal_date: string;
      meal_time: string;
      notes: string;
    }>
  ): Promise<FoodLog> => {
    const response = await apiClient.patch(`/food-logs/${logId}`, data);
    return response.data;
  },

  deleteFoodLog: async (logId: string): Promise<void> => {
    await apiClient.delete(`/food-logs/${logId}`);
  },
};
