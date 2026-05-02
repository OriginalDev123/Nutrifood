"""
Application Constants
Shared constants for meal planning, nutrition calculations, and recommendations
"""

from typing import Dict, List
from decimal import Decimal


# ==========================================
# MEAL TYPE CONSTANTS
# ==========================================

# Meal calorie distribution (as percentage of daily total)
# Used by: MealPlanGenerator, NutritionCalculator
MEAL_DISTRIBUTION: Dict[str, Decimal] = {
    "breakfast": Decimal("0.25"),  # 25% of daily calories
    "lunch": Decimal("0.35"),      # 35% of daily calories
    "dinner": Decimal("0.30"),     # 30% of daily calories
    "snack": Decimal("0.10")       # 10% of daily calories
}

# Food categories suitable for each meal type
# Used by: RecommendationService, NutritionCalculatorCore
MEAL_CATEGORY_MAP: Dict[str, List[str]] = {
    "breakfast": [
        "carbs",           # Ngũ cốc, bánh mì, cơm
        "smart-carbs",     # Carbs lành mạnh
        "protein",         # Protein sources
        "plant-protein",   # Protein thực vật
        "fruit",           # Trái cây
        "probiotics"       # Sữa chua
    ],
    "lunch": [
        "protein",         # Thịt, cá, trứng
        "protein-fat",     # Protein có fat
        "carbs",           # Cơm, bún, phở
        "smart-carbs",     # Carbs tốt
        "fiber",           # Rau củ
        "plant-protein",   # Đậu
        "mixed"            # Món hỗn hợp
    ],
    "dinner": [
        "protein",         # Thịt, cá
        "protein-fat",     # Protein có fat
        "fiber",           # Rau củ
        "carbs",           # Cơm, bún
        "smart-carbs",     # Carbs tốt
        "mixed"            # Món hỗn hợp
    ],
    "snack": [
        "fruit",           # Trái cây
        "protein",         # Protein snacks
        "plant-protein",   # Nuts, seeds
        "probiotics",      # Yogurt
        "carbs"            # Light carbs
    ]
}


# ==========================================
# NUTRITION CONSTANTS
# ==========================================

# Calories per gram of macronutrient
CALORIES_PER_MACRO: Dict[str, int] = {
    "protein": 4,      # 4 calories per gram
    "carbs": 4,        # 4 calories per gram
    "fat": 9           # 9 calories per gram
}

# Default daily fiber target (grams)
DEFAULT_FIBER_TARGET: int = 30

# Macro distribution by goal type (as percentage of total calories)
MACRO_DISTRIBUTION_BY_GOAL: Dict[str, Dict[str, float]] = {
    "lose_weight": {
        "protein": 0.30,   # 30% calories from protein
        "carbs": 0.40,     # 40% calories from carbs
        "fat": 0.30        # 30% calories from fat
    },
    "maintain_weight": {
        "protein": 0.25,
        "carbs": 0.45,
        "fat": 0.30
    },
    "gain_weight": {
        "protein": 0.25,
        "carbs": 0.50,
        "fat": 0.25
    }
}


# ==========================================
# RECIPE MATCHING CONSTANTS
# ==========================================

# Recipe match score thresholds
RECIPE_MATCH_THRESHOLDS: Dict[str, float] = {
    "excellent": 0.90,   # 90%+ ingredients available
    "good": 0.75,        # 75-89% ingredients available
    "partial": 0.50      # 50-74% ingredients available (need to buy some)
}


# ==========================================
# FOOD SEARCH CONSTANTS
# ==========================================

# Fuzzy matching thresholds (0-100)
FUZZY_MATCH_THRESHOLDS: Dict[str, int] = {
    "exact": 100,           # Exact match
    "high_confidence": 85,  # Very similar
    "medium_confidence": 70, # Somewhat similar
    "low_confidence": 60    # Might be similar (show multiple options)
}

# Vietnamese food synonyms for fuzzy matching
VIETNAMESE_FOOD_SYNONYMS: Dict[str, List[str]] = {
    "phở": ["pho"],
    "bún": ["bun"],
    "bánh mì": ["banh mi", "banh my"],
    "cơm": ["com"],
    "chả giò": ["cha gio", "nem rán", "nem ran"],
    "gỏi cuốn": ["goi cuon", "fresh roll", "summer roll"],
    "cà phê": ["ca phe", "coffee"],
    "trà": ["tra", "tea"],
}


# ==========================================
# SERVING SIZE CONSTANTS
# ==========================================

# Common serving sizes in grams
COMMON_SERVING_SIZES: Dict[str, int] = {
    "small": 50,
    "medium": 100,
    "large": 150,
    "extra_large": 200
}

# Portion size recommendations by meal type (grams)
PORTION_SIZE_RECOMMENDATIONS: Dict[str, Dict[str, tuple]] = {
    "breakfast": {
        "protein": (20, 30),    # 20-30g protein foods
        "grains": (50, 100),    # 50-100g grains
        "fruits": (100, 150),   # 100-150g fruits
    },
    "lunch": {
        "protein": (100, 150),  # 100-150g protein foods
        "grains": (150, 200),   # 150-200g grains
        "vegetables": (100, 200), # 100-200g vegetables
    },
    "dinner": {
        "protein": (100, 150),
        "grains": (100, 150),
        "vegetables": (150, 250),
    },
    "snack": {
        "fruits": (80, 120),
        "nuts": (20, 30),
    }
}


# ==========================================
# VALIDATION CONSTANTS
# ==========================================

# Maximum allowed deviation from targets (percentage)
NUTRITION_TOLERANCE: Dict[str, float] = {
    "calories": 0.10,      # ±10% for calories
    "protein": 0.15,       # ±15% for protein (more lenient)
    "carbs": 0.20,         # ±20% for carbs
    "fat": 0.20            # ±20% for fat
}

# Minimum confidence scores for recommendations
MIN_CONFIDENCE_SCORES: Dict[str, float] = {
    "food_suggestion": 0.30,      # Minimum 30% match to suggest
    "recipe_match": 0.50,         # Minimum 50% ingredients available
    "ai_recognition": 0.60        # Minimum 60% confidence from AI vision
}


# ==========================================
# TIME CONSTANTS
# ==========================================

# Maximum cooking time preferences (minutes)
COOKING_TIME_CATEGORIES: Dict[str, int] = {
    "quick": 20,          # Under 20 minutes
    "moderate": 45,       # 20-45 minutes
    "long": 90,           # 45-90 minutes
    "very_long": 180      # Over 90 minutes
}


# ==========================================
# CACHE TTL (seconds)
# ==========================================

CACHE_TTL: Dict[str, int] = {
    "user_goal": 3600,           # 1 hour
    "food_search": 1800,         # 30 minutes
    "recipe_match": 1800,        # 30 minutes
    "chatbot_response": 3600     # 1 hour
}


# ==========================================
# VALIDATION FUNCTIONS
# ==========================================

def validate_meal_type(meal_type: str) -> bool:
    """Check if meal_type is valid"""
    return meal_type in MEAL_DISTRIBUTION


def validate_goal_type(goal_type: str) -> bool:
    """Check if goal_type is valid"""
    return goal_type in MACRO_DISTRIBUTION_BY_GOAL


def get_meal_calorie_target(meal_type: str, daily_target: float) -> float:
    """
    Calculate calorie target for specific meal
    
    Args:
        meal_type: "breakfast" | "lunch" | "dinner" | "snack"
        daily_target: Total daily calorie target
    
    Returns:
        Meal-specific calorie target
    
    Example:
        >>> get_meal_calorie_target("lunch", 2000)
        700.0  # 35% of 2000
    """
    if not validate_meal_type(meal_type):
        raise ValueError(f"Invalid meal_type: {meal_type}")
    
    ratio = float(MEAL_DISTRIBUTION[meal_type])
    return daily_target * ratio


def get_suitable_categories(meal_type: str) -> List[str]:
    """
    Get food categories suitable for meal type
    
    Args:
        meal_type: "breakfast" | "lunch" | "dinner" | "snack"
    
    Returns:
        List of category names
    
    Example:
        >>> get_suitable_categories("breakfast")
        ['Dairy', 'Grains', 'Fruits', 'Eggs', 'Beverages']
    """
    return MEAL_CATEGORY_MAP.get(meal_type, [])
