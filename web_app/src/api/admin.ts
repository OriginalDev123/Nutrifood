/**
 * Admin API endpoints
 * All endpoints require admin authentication
 */

import { apiClient } from './client';

const getHeaders = () => ({
  headers: {
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  },
});

// ==========================================
// TYPES
// ==========================================

export interface AdminUser {
  user_id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  email_verified: boolean;
  created_at: string;
  last_login: string | null;
}

export interface AdminFood {
  food_id: string;
  name_vi: string;
  name_en: string | null;
  category: string;
  cuisine_type: string | null;
  calories_per_100g: number;
  protein_per_100g: number;
  carbs_per_100g: number;
  fat_per_100g: number;
  barcode: string | null;
  image_url: string | null;
  source: string | null;
  is_verified: boolean;
  created_by: string | null;
  creator_name: string | null;
  created_at: string;
}

export interface AdminRecipe {
  recipe_id: string;
  name_vi: string;
  name_en: string | null;
  category: string;
  cuisine_type: string | null;
  prep_time_minutes: number | null;
  cook_time_minutes: number | null;
  servings: number;
  difficulty_level: string | null;
  calories_per_serving: number | null;
  protein_per_serving: number | null;
  carbs_per_serving: number | null;
  fat_per_serving: number | null;
  image_url: string | null;
  source: string | null;
  is_verified: boolean;
  is_public: boolean;
  created_by: string | null;
  creator_name: string | null;
  view_count: number;
  favorite_count: number;
  created_at: string;
}

export interface AdminMealPlan {
  plan_id: string;
  user_id: string;
  user_email: string;
  user_name: string | null;
  plan_name: string;
  start_date: string;
  end_date: string;
  duration_days: number;
  is_active: boolean;
  is_completed: boolean;
  total_meals: number;
  total_calories: number;
  created_at: string;
}

export interface SystemStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  verified_users: number;
  inactive_users: number;
  new_users_today: number;
  new_users_this_week: number;
  new_users_this_month: number;
  total_foods: number;
  verified_foods: number;
  unverified_foods: number;
  total_recipes: number;
  verified_recipes: number;
  unverified_recipes: number;
  total_meal_plans: number;
  active_meal_plans: number;
  total_food_logs: number;
  logs_this_week: number;
  logs_this_month: number;
}

// ==========================================
// USERS API
// ==========================================

export const adminUsersApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    search?: string;
    is_active?: boolean;
    is_admin?: boolean;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.is_active !== undefined) searchParams.set('is_active', String(params.is_active));
    if (params?.is_admin !== undefined) searchParams.set('is_admin', String(params.is_admin));

    const response = await apiClient.get(
      `/admin/users?${searchParams.toString()}`,
      getHeaders()
    );
    return response.data;
  },

  getDetail: async (userId: string) => {
    const response = await apiClient.get(
      `/admin/users/${userId}`,
      getHeaders()
    );
    return response.data;
  },

  updateStatus: async (
    userId: string,
    data: {
      is_active?: boolean;
      is_admin?: boolean;
      email_verified?: boolean;
    }
  ) => {
    const response = await apiClient.patch(
      `/admin/users/${userId}/status`,
      data,
      getHeaders()
    );
    return response.data;
  },

  delete: async (userId: string) => {
    await apiClient.delete(`/admin/users/${userId}`, getHeaders());
  },
};

// ==========================================
// FOODS API
// ==========================================

export const adminFoodsApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    search?: string;
    category?: string;
    is_verified?: boolean;
    source?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.category) searchParams.set('category', params.category);
    if (params?.is_verified !== undefined) searchParams.set('is_verified', String(params.is_verified));
    if (params?.source) searchParams.set('source', params.source);

    const response = await apiClient.get(
      `/admin/foods?${searchParams.toString()}`,
      getHeaders()
    );
    return response.data;
  },

  getDetail: async (foodId: string) => {
    const response = await apiClient.get(
      `/admin/foods/${foodId}`,
      getHeaders()
    );
    return response.data;
  },

  verify: async (foodId: string, isVerified: boolean) => {
    const response = await apiClient.patch(
      `/admin/foods/${foodId}/verify`,
      { is_verified: isVerified },
      getHeaders()
    );
    return response.data;
  },

  delete: async (foodId: string) => {
    await apiClient.delete(`/admin/foods/${foodId}`, getHeaders());
  },
};

// ==========================================
// RECIPES API
// ==========================================

export const adminRecipesApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    search?: string;
    category?: string;
    is_verified?: boolean;
    difficulty?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.category) searchParams.set('category', params.category);
    if (params?.is_verified !== undefined) searchParams.set('is_verified', String(params.is_verified));
    if (params?.difficulty) searchParams.set('difficulty', params.difficulty);

    const response = await apiClient.get(
      `/admin/recipes?${searchParams.toString()}`,
      getHeaders()
    );
    return response.data;
  },

  getDetail: async (recipeId: string) => {
    const response = await apiClient.get(
      `/admin/recipes/${recipeId}`,
      getHeaders()
    );
    return response.data;
  },

  verify: async (recipeId: string, isVerified: boolean) => {
    const response = await apiClient.patch(
      `/admin/recipes/${recipeId}/verify`,
      { is_verified: isVerified },
      getHeaders()
    );
    return response.data;
  },

  toggleVisibility: async (recipeId: string, isPublic: boolean) => {
    const response = await apiClient.patch(
      `/admin/recipes/${recipeId}/visibility?is_public=${isPublic}`,
      {},
      getHeaders()
    );
    return response.data;
  },

  delete: async (recipeId: string) => {
    await apiClient.delete(`/admin/recipes/${recipeId}`, getHeaders());
  },
};

// ==========================================
// MEAL PLANS API
// ==========================================

export const adminMealPlansApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    search?: string;
    is_active?: boolean;
    user_id?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.is_active !== undefined) searchParams.set('is_active', String(params.is_active));
    if (params?.user_id) searchParams.set('user_id', params.user_id);

    const response = await apiClient.get(
      `/admin/meal-plans?${searchParams.toString()}`,
      getHeaders()
    );
    return response.data;
  },

  getDetail: async (planId: string) => {
    const response = await apiClient.get(
      `/admin/meal-plans/${planId}`,
      getHeaders()
    );
    return response.data;
  },

  delete: async (planId: string) => {
    await apiClient.delete(`/admin/meal-plans/${planId}`, getHeaders());
  },
};

// ==========================================
// ANALYTICS API
// ==========================================

export const adminAnalyticsApi = {
  getStats: async () => {
    const response = await apiClient.get('/admin/stats', getHeaders());
    return response.data;
  },

  getOverview: async (): Promise<SystemStats> => {
    const response = await apiClient.get('/admin/analytics/overview', getHeaders());
    return response.data;
  },
};
