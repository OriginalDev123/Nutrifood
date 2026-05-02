export interface User {
  user_id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  email_verified: boolean;
  created_at: string;
  last_login: string | null;
}

export interface UserProfile {
  profile_id: string;
  user_id: string;
  full_name?: string | null;
  email?: string | null;
  email_verified?: boolean;
  created_at?: string;
  last_login?: string | null;
  date_of_birth: string | null;
  gender: 'male' | 'female' | 'other' | null;
  height_cm: number | null;
  activity_level: string | null;
  profile_image_url?: string | null;
  timezone?: string | null;
  language?: string | null;
  bmi?: number;
  bmi_category?: string;
  age?: number;
}

export interface UserGoal {
  goal_id: string;
  user_id: string;
  goal_type: 'weight_loss' | 'weight_gain' | 'maintain' | 'healthy_lifestyle';
  current_weight_kg: number;
  target_weight_kg: number | null;
  target_date: string | null;
  daily_calorie_target: number | null;
  protein_target_g: number | null;
  carbs_target_g: number | null;
  fat_target_g: number | null;
  is_active: boolean;
}

export interface FoodServing {
  serving_id: string;
  food_id: string;
  serving_size_g: number;
  serving_unit: string;
  description: string | null;
  is_default: boolean;
}

export interface Food {
  food_id: string;
  name_vi: string;
  name_en: string | null;
  description?: string | null;
  category: string;
  cuisine_type?: string | null;
  calories_per_100g: number;
  protein_per_100g: number;
  carbs_per_100g: number;
  fat_per_100g: number;
  fiber_per_100g?: number | null;
  sugar_per_100g?: number | null;
  sodium_per_100g?: number | null;
  barcode?: string | null;
  image_url?: string | null;
  source?: string | null;
  created_by?: string | null;
  brand?: string | null;
  notes?: string | null;
  servings?: FoodServing[];
  is_verified: boolean;
}

export interface FoodSearchResponse {
  total: number;
  foods: Food[];
  page: number;
  page_size: number;
}

export interface FoodLog {
  log_id: string;
  food_name: string;
  serving_size_g: number;
  quantity: number;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  meal_date: string;
  meal_time: string | null;
  notes: string | null;
}

export interface DailySummary {
  date: string;
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  meal_count: number;
  meals_breakdown: Record<string, number>;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface WeightLog {
  weight_log_id: string;
  user_id: string;
  weight_kg: number;
  measured_date: string;
  created_at: string;
  notes?: string | null;
}

export interface ChatSourceDocument {
  title: string;
  relevance_score: number;
}

export interface ChatAskRequest {
  question: string;
  session_id?: string;
  user_context?: {
    user_id?: string;
    current_weight?: number;
    goal_type?: string;
    daily_target?: number;
    consumed_today?: number;
  };
  top_k?: number;
  score_threshold?: number;
}

export interface ChatAskResponse {
  answer: string;
  session_id: string;
  sources: ChatSourceDocument[];
  processing_time_ms: number;
  retrieved_docs: number;
}