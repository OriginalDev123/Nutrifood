# app/services/__init__.py

# 1. Auth & User
from .auth_service import create_user, authenticate_user, get_user_by_id
from .user_service import get_user_profile, update_user_profile, calculate_bmi, calculate_age

# 2. Food & Logging
from .food_service import get_foods, search_foods, get_food_by_id, get_food_by_barcode, create_food, get_categories
from .food_log_service import log_meal, get_daily_summary, get_food_logs_by_date, delete_food_log, log_weight, get_weight_history_paginated, get_latest_weight

# 3. Goals & Analytics
from .goal_service import create_user_goal, get_user_goals, get_active_goal, update_goal, calculate_bmr, calculate_tdee, deactivate_goal
from .analytics_service import get_nutrition_trends, get_weight_progress, get_macro_distribution, get_calorie_comparison, get_meal_patterns, get_goal_progress, get_food_frequency

# 4. Recipes
from .recipe_service import create_recipe, get_recipes, get_recipe_by_id, search_recipes, update_recipe, delete_recipe, add_favorite, remove_favorite

# 5. Meal Plan
from .meal_plan_service import create_meal_plan, add_meal_plan_item, get_user_meal_plans, get_meal_plan_with_items,delete_meal_plan,update_meal_plan,delete_meal_plan_item,mark_plan_completed

from .meal_plan_generator import generate_meal_plan, generate_shopping_list, analyze_meal_plan, regenerate_day
