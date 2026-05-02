import { aiServiceClient } from './client';

export interface VisionDatabaseMatch {
  item_type: 'food' | 'recipe';
  item_id: string;
  name_vi: string;
  name_en?: string | null;
  category?: string | null;
  calories_per_serving?: number | null;
  protein_per_serving?: number | null;
  carbs_per_serving?: number | null;
  fat_per_serving?: number | null;
  calories_per_100g?: number | null;
  protein_per_100g?: number | null;
  carbs_per_100g?: number | null;
  fat_per_100g?: number | null;
  match_score?: number | null;
  matched_name?: string | null;
}

export interface VisionPortionPreset {
  preset_id: string;
  size_label: string;
  display_name_vi?: string | null;
  display_name_en?: string | null;
  unit_type?: string | null;
  unit_display_vi?: string | null;
  unit_display_en?: string | null;
  grams: number;
  is_default: boolean;
  sort_order: number;
  item_type: 'food' | 'recipe';
  food_id?: string | null;
  food_name?: string | null;
  recipe_id?: string | null;
  recipe_name?: string | null;
}

export interface VisionAnalyzeResponse {
  is_food: boolean;
  food_name: string;
  food_type: 'recipe' | 'ingredient';
  components: string[];
  description: string;
  confidence: number;
  database_match?: VisionDatabaseMatch | null;
  alternatives: VisionDatabaseMatch[];
  portion_presets: VisionPortionPreset[];
  processing_time_ms: number;
  needs_retry: boolean;
  retry_suggestions: string[];
  from_cache: boolean;
  recovery_mode?: 'partial' | 'minimal' | 'plaintext' | null;
  result_quality?: 'high' | 'medium' | 'low' | 'retry_needed' | 'failed' | null;
  inferred_from_user_hint?: boolean | null;
  error?: string | null;
}

export interface VisionCalculateNutritionRequest {
  vision_context: VisionAnalyzeResponse;
  preset_id?: string;
  portion_grams?: number;
  quantity: number;
}

export interface VisionNutritionData {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface VisionCalculateNutritionResponse {
  item_type: 'food' | 'recipe';
  item_id: string;
  item_name: string;
  quantity: number;
  selected_portion_grams: number;
  total_portion_grams: number;
  selected_portion_label?: string | null;
  selected_preset_id?: string | null;
  nutrition: VisionNutritionData;
  reference_portion_grams?: number | null;
  reference_portion_label?: string | null;
}

export interface VisionLogMealRequest extends VisionCalculateNutritionRequest {
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  meal_date: string;
  meal_time?: string;
  notes?: string;
  image_url?: string;
}

export interface VisionLogMealResponse {
  logged_entry: Record<string, unknown>;
  daily_summary: Record<string, unknown>;
  item_type: 'food' | 'recipe';
  item_id: string;
  item_name: string;
  quantity: number;
  selected_portion_grams: number;
  total_portion_grams: number;
  selected_portion_label?: string | null;
  selected_preset_id?: string | null;
}

export interface VisionHealthResponse {
  status: 'healthy' | 'unhealthy';
  message: string;
  vision_enabled: boolean;
  model?: string;
}

export const visionApi = {
  analyzeImage: async (imageFile: File, userHint?: string): Promise<VisionAnalyzeResponse> => {
    const formData = new FormData();
    formData.append('image', imageFile);
    if (userHint?.trim()) {
      formData.append('user_hint', userHint.trim());
    }

    const response = await aiServiceClient.post('/vision/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  calculateNutrition: async (payload: VisionCalculateNutritionRequest): Promise<VisionCalculateNutritionResponse> => {
    const response = await aiServiceClient.post('/vision/calculate-nutrition', payload);
    return response.data;
  },

  logMeal: async (payload: VisionLogMealRequest): Promise<VisionLogMealResponse> => {
    const response = await aiServiceClient.post('/vision/log-meal', payload);
    return response.data;
  },

  healthCheck: async (): Promise<VisionHealthResponse> => {
    const response = await aiServiceClient.get('/vision/health');
    return response.data;
  },
};
