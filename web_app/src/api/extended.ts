// Extended types for Analytics, Meal Plan, Recipe, Upload
// This file extends the base types from api/types.ts

// ==========================================
// ANALYTICS TYPES
// ==========================================

export interface NutritionTrend {
  date: string;
  total_calories: number;
  protein: number;
  carbs: number;
  fat: number;
  meal_count: number;
}

export interface NutritionTrendsResponse {
  start_date: string;
  end_date: string;
  group_by: 'day' | 'week' | 'month';
  data_points: number;
  trends: NutritionTrend[];
}

export interface MacroDistribution {
  date: string;
  protein_grams: number;
  protein_calories: number;
  protein_percentage: number;
  carbs_grams: number;
  carbs_calories: number;
  carbs_percentage: number;
  fat_grams: number;
  fat_calories: number;
  fat_percentage: number;
  total_calories: number;
}

export interface CalorieComparisonItem {
  date: string;
  actual: number;
  target: number;
  difference: number;
  status: 'over' | 'under' | 'on_track';
}

export interface CalorieComparisonResponse {
  start_date: string;
  end_date: string;
  days: CalorieComparisonItem[];
  adherence_percentage: number;
  days_on_track: number;
  total_days: number;
}

export interface MealPattern {
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  count: number;
  avg_calories: number;
  avg_percentage: number;
}

export interface MealPatternsResponse {
  days_analyzed: number;
  total_meals: number;
  patterns: Record<string, MealPattern>;
}

export interface WeightProgressItem {
  date: string;
  weight_kg: number;
}

export interface WeightProgressResponse {
  days_analyzed: number;
  start_date: string;
  end_date: string;
  starting_weight: number;
  current_weight: number;
  target_weight: number | null;
  change_kg: number;
  change_percentage: number;
  trend: 'gaining' | 'losing' | 'stable' | 'no_data';
  history: WeightProgressItem[];
}

export interface GoalProgressResponse {
  goal_id: string;
  goal_type: string;
  start_weight: number;
  current_weight: number;
  target_weight: number;
  progress_percentage: number;
  days_elapsed: number;
  days_remaining: number;
  status: 'on_track' | 'behind' | 'achieved';
  daily_calorie_target: number;
  avg_daily_calories: number;
}

export interface FoodFrequencyItem {
  food_id: string;
  name_vi: string;
  name_en: string | null;
  times_logged: number;
  total_calories: number;
  avg_calories_per_serving: number;
}

export interface WeeklySummary {
  period: string;
  start_date: string;
  end_date: string;
  summary: {
    days_logged: number;
    avg_daily_calories: number;
    total_meals: number;
    weight_change_kg: number;
    weight_trend: 'gaining' | 'losing' | 'stable' | 'no_data';
  };
  daily_nutrition: NutritionTrend[];
  meal_patterns: Record<string, MealPattern>;
}

// ==========================================
// MEAL PLAN TYPES
// ==========================================

export interface MealPlan {
  plan_id: string;
  user_id: string;
  plan_name: string;
  start_date: string;
  end_date: string;
  total_calories?: number;
  total_days?: number;
  status?: 'active' | 'completed' | 'archived';
  preferences: MealPlanPreferences | null;
  created_at: string;
  is_active?: boolean;
  is_completed?: boolean;
}

export interface MealPlanPreferences {
  categories?: string[];
  tags?: string[];
  max_cook_time?: number;
  exclusions?: string[];
  preferred_cuisines?: string[];
}

export interface MealPlanDay {
  day_number: number;
  date: string;
  items: MealPlanItem[];
  total_calories: number;
}

export interface MealPlanItem {
  item_id: string;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  recipe_id?: string;
  recipe_name?: string;
  food_id?: string;
  food_name?: string;
  serving_size_g: number;
  servings?: number;
  quantity?: number;
  calories?: number;
  protein?: number;
  protein_g?: number;
  carbs?: number;
  carbs_g?: number;
  fat?: number;
  fat_g?: number;
  image_url?: string;
  notes?: string;
}

export interface MealPlanWithItems extends MealPlan {
  days: MealPlanDay[];
  prep_time_minutes?: number | null;
  cook_time_minutes?: number | null;
  servings?: number;
  difficulty_level?: string | null;
  total_protein?: number;
  total_recipes?: number;
}

export interface ShoppingListItem {
  ingredient_name: string;
  food_id: string | null;
  total_quantity: number;
  unit: string;
  recipes: string[];
  is_available: boolean;
}

export interface ShoppingListResponse {
  plan_name: string;
  start_date: string;
  end_date: string;
  shopping_list: ShoppingListItem[];
  total_items: number;
  recipes_count: number;
}

export interface MealPlanAnalysis {
  plan_id: string;
  plan_name: string;
  avg_daily_calories: number;
  avg_daily_protein: number;
  avg_daily_carbs: number;
  avg_daily_fat: number;
  calorie_variance: number;
  goal_adherence: number;
  variety_score: number;
}

// ==========================================
// RECIPE TYPES
// ==========================================

export interface Recipe {
  recipe_id: string;
  creator_id: string;
  name_vi: string;
  name_en: string | null;
  description: string | null;
  category: string;
  difficulty_level: 'easy' | 'medium' | 'hard';
  prep_time_minutes: number;
  cook_time_minutes: number;
  servings: number;
  calories_per_serving: number;
  protein_per_serving: number;
  carbs_per_serving: number;
  fat_per_serving: number;
  image_url: string | null;
  tags: string[];
  view_count: number;
  favorite_count: number;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface RecipeIngredient {
  ingredient_id: string;
  food_id: string | null;
  ingredient_name: string;
  quantity: number;
  unit: string;
  notes: string | null;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
}

export interface RecipeDetail extends Recipe {
  ingredients: RecipeIngredient[];
  instructions?: string[] | string | null;
  instructions_steps?: Array<string | { step?: number; text?: string }> | null;
  is_favorited: boolean;
  substitutions?: Substitution[];
}

export interface Substitution {
  ingredient_name: string;
  alternatives: SubstitutionAlternative[];
}

export interface SubstitutionAlternative {
  food_id: string;
  name_vi: string;
  name_en: string | null;
  reason: string;
}

export interface RecipeFavorite {
  favorite_id: string;
  user_id: string;
  recipe_id: string;
  added_at: string;
  notes: string | null;
}

export interface MatchIngredient {
  ingredient_id: string;
  food_name: string;
  quantity: number;
  unit: string;
}

export interface RecipeMatch {
  recipe: Recipe;
  match_score: number;
  match_level: 'excellent' | 'good' | 'partial';
  matched_ingredients: string[];
  missing_ingredients: string[];
  calories_per_serving: number;
}

export interface MatchIngredientsResponse {
  matches: RecipeMatch[];
  total_count: number;
  user_ingredient_count: number;
}

// ==========================================
// UPLOAD TYPES
// ==========================================

export interface UploadResponse {
  image_url: string;
  filename: string;
  original_filename: string;
  size_bytes: number;
}

export interface BulkUploadResponse {
  uploaded_count: number;
  failed_count: number;
  files: Array<{
    original_filename: string;
    image_url: string;
    filename: string;
  } & { error?: string }>;
}

// ==========================================
// ADMIN TYPES
// ==========================================

export interface AdminStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  verified_users: number;
  new_users_today: number;
  new_users_this_week: number;
  new_users_this_month: number;
}

export interface UserListItem {
  user_id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  email_verified: boolean;
  created_at: string;
  last_login: string | null;
}

export interface PaginatedUserList {
  total: number;
  skip: number;
  limit: number;
  users: UserListItem[];
}

// ==========================================
// API ERROR TYPE
// ==========================================

export interface ApiError {
  success: false;
  data: null;
  message: string;
  detail?: string;
}

export interface ApiResponse<T> {
  success: true;
  data: T;
  message: string;
}

// ==========================================
// AI INSIGHTS TYPES (for Analytics)
// ==========================================

export interface AIWeeklyInsightsResponse {
  period: string;
  summary: string;
  highlights: string[];
  concerns: string[];
  recommendations: string[];
  generated_at: string;
}

export interface AIGoalInsightsResponse {
  status_message: string;
  progress_assessment: string;
  recommendations: string[];
  motivation: string;
  generated_at: string;
}

export interface AITrendInsightsResponse {
  period_days: number;
  analysis: {
    avg_calories: number;
    avg_protein: number;
    calorie_trend: 'increasing' | 'decreasing' | 'stable';
    protein_trend: 'increasing' | 'decreasing' | 'stable';
    consistent_days: number;
  };
  insights: string;
  generated_at: string;
}

// ==========================================
// CALORIE NOTIFICATION TYPES
// ==========================================

export interface CalorieNotification {
  type: 'success' | 'warning' | 'danger';
  message: string;
  suggestion?: string;
  remaining?: number;
}

// ==========================================
// NUTRITION ADVICE TYPES (AI-powered personalized advice)
// ==========================================

export interface NutritionAdviceResponse {
  summary: string;
  highlights: string[];
  concerns: string[];
  recommendations: string[];
  motivational_tip: string;
  period: 'day' | 'week' | 'month';
  days_analyzed: number;
  generated_at: string;
  raw_data?: {
    nutrition_trends_count: number;
    weight_history_count: number;
  };
}

export interface QuickAdviceResponse {
  quick_tip: string;
  action: string;
  why: string;
  date: string;
  generated_at: string;
}

export interface WeightAnalysis {
  progress: string;
  on_track: boolean;
  reasoning: string;
}

export interface NutritionAnalysis {
  calorie_adherence: string;
  protein_quality: string;
  consistency: string;
}

export interface ProgressReportResponse {
  period: 'week' | 'month';
  overall_score: number;
  summary: string;
  weight_analysis: WeightAnalysis;
  nutrition_analysis: NutritionAnalysis;
  achievements: string[];
  areas_for_improvement: string[];
  next_week_tips: string[];
  motivation: string;
  days_analyzed: number;
  generated_at: string;
}