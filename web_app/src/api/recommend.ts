import { apiClient } from './client';

export type RecommendationMealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

export interface RecommendedFood {
  food_id: string;
  name_vi: string;
  name_en: string | null;
  confidence: number;
  reason: string;
  serving_suggestion: string;
  nutrition_per_100g: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
  };
}

export interface NextMealRecommendationsResponse {
  meal_type: RecommendationMealType;
  date: string;
  remaining_nutrients: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
  };
  suggestions: RecommendedFood[];
  processing_time_ms: number;
}

export interface MealTimingResponse {
  suggested_meal_type: RecommendationMealType;
  reason: string;
  already_logged: RecommendationMealType[];
}

export const recommendApi = {
  getNextMealSuggestions: async (
    mealType: RecommendationMealType,
    date?: string
  ): Promise<NextMealRecommendationsResponse> => {
    const response = await apiClient.get('/recommendations/next-meal', {
      params: { meal_type: mealType, date },
    });
    return response.data;
  },

  getMealTiming: async (date?: string): Promise<MealTimingResponse> => {
    const response = await apiClient.get('/recommendations/meal-timing', {
      params: { date },
    });
    return response.data;
  },

  healthCheck: async (): Promise<{
    status: string;
    service: string;
    type: string;
    features: string[];
  }> => {
    const response = await apiClient.get('/recommendations/health');
    return response.data;
  },
};
