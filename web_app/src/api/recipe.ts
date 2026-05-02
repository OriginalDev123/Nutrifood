import { apiClient } from './client';
import type {
  Recipe,
  RecipeDetail,
  RecipeIngredient,
  MatchIngredientsResponse,
} from './extended';

// Recipe list params
export interface GetRecipesParams {
  skip?: number;
  limit?: number;
  category?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  max_cook_time?: number;
  tags?: string;
  verified_only?: boolean;
}

export interface CreateRecipeData {
  name_vi: string;
  category: string;
  servings: number;
  prep_time_minutes?: number;
  cook_time_minutes?: number;
  difficulty_level?: 'easy' | 'medium' | 'hard';
  description?: string;
  image_url?: string;
  tags?: string[];
  ingredients: RecipeIngredient[];
  instructions: string;
}

export const recipeApi = {
  // Get recipes with optional filtering
  getRecipes: async (params?: GetRecipesParams): Promise<Recipe[]> => {
    const response = await apiClient.get('/recipes', { params });
    return response.data;
  },

  // Search recipes by name or description
  searchRecipes: async (query: string, limit: number = 20): Promise<Recipe[]> => {
    const response = await apiClient.get('/recipes/search', {
      params: { q: query, limit },
    });
    return response.data;
  },

  // Get recipe detail with ingredients
  getRecipeDetail: async (recipeId: string): Promise<RecipeDetail> => {
    const response = await apiClient.get(`/recipes/${recipeId}`);
    return response.data;
  },

  // Get recipe categories
  getCategories: async (): Promise<string[]> => {
    const response = await apiClient.get('/recipes/categories');
    return response.data;
  },

  // Get popular recipes
  getPopular: async (
    limit: number = 10,
    timePeriod: 'all_time' | 'month' | 'week' = 'all_time'
  ): Promise<Recipe[]> => {
    const response = await apiClient.get('/recipes/popular', {
      params: { limit, time_period: timePeriod },
    });
    return response.data;
  },

  // Get personalized recommendations
  getRecommendations: async (limit: number = 10): Promise<Recipe[]> => {
    const response = await apiClient.get('/recipes/recommendations', {
      params: { limit },
    });
    return response.data;
  },

  // Get user's favorite recipes
  getMyFavorites: async (skip: number = 0, limit: number = 20): Promise<Recipe[]> => {
    const response = await apiClient.get('/recipes/favorites/my', {
      params: { skip, limit },
    });
    return response.data;
  },

  // Add recipe to favorites
  addFavorite: async (
    recipeId: string,
    notes?: string
  ): Promise<{ favorite_id: string; notes: string | null }> => {
    const response = await apiClient.post(`/recipes/${recipeId}/favorite`, { notes });
    return response.data;
  },

  // Remove recipe from favorites
  removeFavorite: async (recipeId: string): Promise<void> => {
    await apiClient.delete(`/recipes/${recipeId}/favorite`);
  },

  // Create new recipe
  createRecipe: async (data: CreateRecipeData): Promise<RecipeDetail> => {
    const response = await apiClient.post('/recipes', data);
    return response.data;
  },

  // Update recipe
  updateRecipe: async (
    recipeId: string,
    data: Partial<CreateRecipeData>
  ): Promise<RecipeDetail> => {
    const response = await apiClient.patch(`/recipes/${recipeId}`, data);
    return response.data;
  },

  // Delete recipe (soft delete)
  deleteRecipe: async (recipeId: string): Promise<void> => {
    await apiClient.delete(`/recipes/${recipeId}`);
  },

  // Get recipe substitutions
  getSubstitutions: async (
    recipeId: string
  ): Promise<{
    recipe_id: string;
    recipe_name: string;
    substitutions: Array<{
      ingredient_name: string;
      alternatives: Array<{
        food_id: string;
        name_vi: string;
        name_en: string | null;
        reason: string;
      }>;
    }>;
  }> => {
    const response = await apiClient.get(`/recipes/${recipeId}/substitutions`);
    return response.data;
  },

  // Get recipe portions/presets
  getPortions: async (
    recipeId: string
  ): Promise<
    Array<{
      preset_id: string;
      size_label: string;
      display_name_vi: string;
      display_name_en: string;
      unit_type: string;
      unit_display_vi: string;
      grams: number;
      is_default: boolean;
      sort_order: number;
      item_type: string;
      recipe_id: string;
      recipe_name: string;
    }>
  > => {
    const response = await apiClient.get(`/recipes/${recipeId}/portions`);
    return response.data;
  },

  // Match recipes by available ingredients
  matchByIngredients: async (
    ingredientIds: string[],
    minMatchScore: number = 0.5,
    limit: number = 20,
    category?: string
  ): Promise<MatchIngredientsResponse> => {
    const response = await apiClient.post('/recipes/match-ingredients', {
      ingredient_ids: ingredientIds,
      min_match_score: minMatchScore,
      limit,
      category,
    });
    return response.data;
  },

  // Generate shopping list for multiple recipes
  generateShoppingList: async (
    recipeIds: string[],
    availableIngredientIds?: string[]
  ): Promise<{
    shopping_list: Array<{
      ingredient_name: string;
      food_id: string | null;
      total_quantity: number;
      unit: string;
      recipes: string[];
      is_available: boolean;
    }>;
    total_items: number;
    recipes_count: number;
  }> => {
    const response = await apiClient.post('/recipes/shopping-list', {
      recipe_ids: recipeIds,
      available_ingredient_ids: availableIngredientIds,
    });
    return response.data;
  },

  // Verify recipe (admin only)
  verifyRecipe: async (recipeId: string): Promise<RecipeDetail> => {
    const response = await apiClient.patch(`/recipes/${recipeId}/verify`);
    return response.data;
  },
};