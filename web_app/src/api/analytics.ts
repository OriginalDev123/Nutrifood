import { apiClient, getAuthToken } from './client';
import type {
  NutritionTrendsResponse,
  MacroDistribution,
  CalorieComparisonResponse,
  MealPatternsResponse,
  WeightProgressResponse,
  GoalProgressResponse,
  FoodFrequencyItem,
  WeeklySummary,
  AIWeeklyInsightsResponse,
  AIGoalInsightsResponse,
  AITrendInsightsResponse,
  NutritionAdviceResponse,
  QuickAdviceResponse,
  ProgressReportResponse,
} from './extended';

export const analyticsApi = {
  // Nutrition Trends - Get nutrition data over time period
  getNutritionTrends: async (
    startDate: string,
    endDate: string,
    groupBy: 'day' | 'week' | 'month' = 'day'
  ): Promise<NutritionTrendsResponse> => {
    const response = await apiClient.get('/nutrition-trends', {
      params: { start_date: startDate, end_date: endDate, group_by: groupBy },
    });
    return response.data;
  },

  // Weight Progress - Get weight history with trend analysis
  getWeightProgress: async (days: number = 30): Promise<WeightProgressResponse> => {
    const response = await apiClient.get('/weight-progress', {
      params: { days },
    });
    return response.data;
  },

  // Macro Distribution - Get macronutrient breakdown for a specific date
  getMacroDistribution: async (targetDate: string): Promise<MacroDistribution> => {
    const response = await apiClient.get('/macro-distribution', {
      params: { target_date: targetDate },
    });
    return response.data;
  },

  // Calorie Comparison - Compare actual vs target calories over date range
  getCalorieComparison: async (
    startDate: string,
    endDate: string
  ): Promise<CalorieComparisonResponse> => {
    const response = await apiClient.get('/calorie-comparison', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },

  // Meal Patterns - Analyze meal timing patterns
  getMealPatterns: async (days: number = 30): Promise<MealPatternsResponse> => {
    const response = await apiClient.get('/meal-patterns', {
      params: { days },
    });
    return response.data;
  },

  // Goal Progress - Get progress towards active goal
  getGoalProgress: async (): Promise<GoalProgressResponse> => {
    const response = await apiClient.get('/goal-progress');
    return response.data;
  },

  // Food Frequency - Get most frequently logged foods
  getFoodFrequency: async (
    days: number = 30,
    limit: number = 10
  ): Promise<{ days_analyzed: number; top_foods: FoodFrequencyItem[] }> => {
    const response = await apiClient.get('/food-frequency', {
      params: { days, limit },
    });
    return response.data;
  },

  // Weekly Summary - Get comprehensive weekly summary
  getWeeklySummary: async (): Promise<WeeklySummary> => {
    const response = await apiClient.get('/weekly-summary');
    return response.data;
  },

  // ==========================================
  // AI-POWERED INSIGHTS (from AI Service)
  // ==========================================

  getAIWeeklyInsights: async (language: string = 'vi'): Promise<AIWeeklyInsightsResponse> => {
    const token = getAuthToken();
    const response = await apiClient.post(
      '/analytics/weekly-insights',
      { language },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  },

  getAIGoalInsights: async (language: string = 'vi'): Promise<AIGoalInsightsResponse> => {
    const token = getAuthToken();
    const response = await apiClient.post(
      '/analytics/goal-insights',
      { language },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  },

  getAINutritionTrendInsights: async (days: number = 30): Promise<AITrendInsightsResponse> => {
    const token = getAuthToken();
    const response = await apiClient.post(
      `/analytics/nutrition-trend-insights?days=${days}`,
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  },

  // Weight logging
  logWeight: async (weight: number, date: string) => {
    const response = await apiClient.post('/food-logs/weight', {
      weight_kg: weight,
      measured_date: date,
    });
    return response.data;
  },

  // ==========================================
  // NUTRITION ADVICE (AI-powered personalized advice)
  // ==========================================

  getNutritionAdvice: async (
    days: number = 7,
    period: 'day' | 'week' | 'month' = 'week',
    language: string = 'vi'
  ): Promise<NutritionAdviceResponse> => {
    const token = getAuthToken();
    const response = await apiClient.post(
      '/analytics/nutrition-advice',
      { days, period, language },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  },

  getQuickAdvice: async (
    targetDate?: string,
    language: string = 'vi'
  ): Promise<QuickAdviceResponse> => {
    const token = getAuthToken();
    const response = await apiClient.post(
      '/analytics/quick-advice',
      { target_date: targetDate, language },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  },

  getProgressReport: async (
    period: 'week' | 'month' = 'week',
    language: string = 'vi'
  ): Promise<ProgressReportResponse> => {
    const token = getAuthToken();
    const response = await apiClient.post(
      '/analytics/progress-report',
      { period, language },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  },
};