"""
Analytics Service
Business logic for user nutrition analytics and progress tracking
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from uuid import UUID

from app.models.food_log import FoodLog, WeightLog
from app.models.user import UserGoal


# ==========================================
# NUTRITION TRENDS
# ==========================================

def get_nutrition_trends(
    db: Session,
    user_id: UUID,
    start_date: date,
    end_date: date,
    group_by: str = "day"  # day, week, month
) -> List[Dict]:
    """
    Get nutrition trends over time period
    
    Returns daily/weekly/monthly aggregated nutrition data
    """
    
    # Validate date range
    if end_date < start_date:
        raise ValueError("end_date must be after start_date")
    
    if (end_date - start_date).days > 365:
        raise ValueError("Date range cannot exceed 1 year")
    
    # Build query based on grouping
    if group_by == "day":
        date_field = FoodLog.meal_date
    elif group_by == "week":
        # PostgreSQL: date_trunc('week', meal_date)
        from sqlalchemy import literal_column
        date_field = func.date_trunc('week', FoodLog.meal_date)
    elif group_by == "month":
        date_field = func.date_trunc('month', FoodLog.meal_date)
    else:
        raise ValueError("group_by must be 'day', 'week', or 'month'")
    
    # Query aggregated data
    results = db.query(
        date_field.label('date'),
        func.sum(FoodLog.calories).label('total_calories'),
        func.sum(FoodLog.protein_g).label('total_protein'),
        func.sum(FoodLog.carbs_g).label('total_carbs'),
        func.sum(FoodLog.fat_g).label('total_fat'),
        func.count(FoodLog.log_id).label('meal_count')
    ).filter(
        FoodLog.user_id == user_id,
        FoodLog.meal_date >= start_date,
        FoodLog.meal_date <= end_date
    ).group_by(date_field).order_by(date_field).all()
    
    # Format response
    trends = []
    for row in results:
        trends.append({
            "date": row.date.strftime('%Y-%m-%d') if isinstance(row.date, date) else str(row.date),
            "total_calories": float(row.total_calories or 0),
            "total_protein_g": float(row.total_protein or 0),
            "total_carbs_g": float(row.total_carbs or 0),
            "total_fat_g": float(row.total_fat or 0),
            "meal_count": row.meal_count or 0
        })
    
    return trends


# ==========================================
# WEIGHT PROGRESS
# ==========================================

def get_weight_progress(
    db: Session,
    user_id: UUID,
    days: int = 30
) -> Dict:
    """
    Get weight progress with trend analysis.

    Logic:
    - starting_weight: tu Goal.current_weight_kg (cân khi tạo mục tiêu), fallback sang WeightLog đầu tiên
    - current_weight: từ WeightLog mới nhất
    - change_kg = current_weight - starting_weight (so sánh với cân lúc tạo mục tiêu)
    - target_weight: từ Goal.target_weight_kg
    """

    if days < 1 or days > 365:
        raise ValueError("days must be between 1 and 365")

    # 1. Lấy cân nặng ban đầu từ Goal (cân khi tạo mục tiêu)
    goal = db.query(UserGoal).filter(
        UserGoal.user_id == user_id,
        UserGoal.is_active == True,
        UserGoal.is_deleted == False
    ).first()

    goal_starting_weight = float(goal.current_weight_kg) if goal and goal.current_weight_kg else None
    goal_target_weight = float(goal.target_weight_kg) if goal and goal.target_weight_kg else None

    # 2. Lấy lịch sử weight từ WeightLog trong khoảng 'days' ngày
    cutoff_date = date.today() - timedelta(days=days)
    weight_logs = db.query(WeightLog).filter(
        WeightLog.user_id == user_id,
        WeightLog.measured_date >= cutoff_date,
        WeightLog.is_deleted == False
    ).order_by(WeightLog.measured_date.asc()).all()

    # 3. Xác định starting_weight:
    #    Ưu tiên: goal_starting_weight (cân lúc tạo mục tiêu)
    #    Fallback: bản ghi WeightLog đầu tiên trong khoảng days
    if goal_starting_weight is not None:
        starting_weight = goal_starting_weight
    elif weight_logs:
        starting_weight = float(weight_logs[0].weight_kg)
    else:
        starting_weight = None

    # 4. Xác định current_weight: bản ghi WeightLog mới nhất
    if weight_logs:
        current_weight = float(weight_logs[-1].weight_kg)
    else:
        current_weight = None

    # 5. Tính change_kg (so với cân lúc tạo mục tiêu)
    if starting_weight is not None and current_weight is not None:
        change_kg = current_weight - starting_weight
        change_percent = (change_kg / starting_weight * 100) if starting_weight > 0 else 0
    else:
        change_kg = 0
        change_percent = 0

    # 6. Xác định trend dựa trên change_kg
    if starting_weight is None or current_weight is None:
        trend = "no_data"
    elif abs(change_kg) < 0.5:
        trend = "stable"
    elif change_kg > 0:
        trend = "gaining"
    else:
        trend = "losing"

    # 7. Format history (bỏ qua bản ghi trùng ngày, chỉ giữ bản ghi mới nhất)
    seen_dates = set()
    history = []
    for log in weight_logs:
        date_str = log.measured_date.strftime('%Y-%m-%d')
        if date_str not in seen_dates:
            seen_dates.add(date_str)
            history.append({
                "date": date_str,
                "weight_kg": float(log.weight_kg),
                "notes": log.notes
            })

    return {
        "history": history,
        "starting_weight": starting_weight,
        "current_weight": current_weight,
        "target_weight": goal_target_weight,
        "change_kg": round(change_kg, 2),
        "change_percentage": round(change_percent, 2),
        "trend": trend,
        "days_tracked": len(history)
    }


# ==========================================
# MACRO DISTRIBUTION
# ==========================================

def get_macro_distribution(
    db: Session,
    user_id: UUID,
    target_date: date
) -> Dict:
    """
    Get macronutrient distribution for a specific date
    
    Returns calories from protein/carbs/fat and percentages
    """
    
    # Get daily totals
    summary = db.query(
        func.sum(FoodLog.protein_g).label('total_protein'),
        func.sum(FoodLog.carbs_g).label('total_carbs'),
        func.sum(FoodLog.fat_g).label('total_fat'),
        func.sum(FoodLog.calories).label('total_calories')
    ).filter(
        FoodLog.user_id == user_id,
        FoodLog.meal_date == target_date
    ).first()
    
    total_protein = float(summary.total_protein or 0)
    total_carbs = float(summary.total_carbs or 0)
    total_fat = float(summary.total_fat or 0)
    total_calories = float(summary.total_calories or 0)
    
    # Calculate calories from each macro
    # Protein: 4 cal/g, Carbs: 4 cal/g, Fat: 9 cal/g
    protein_calories = total_protein * 4
    carbs_calories = total_carbs * 4
    fat_calories = total_fat * 9
    
    calculated_total = protein_calories + carbs_calories + fat_calories
    
    # Calculate percentages
    if calculated_total > 0:
        protein_percent = (protein_calories / calculated_total) * 100
        carbs_percent = (carbs_calories / calculated_total) * 100
        fat_percent = (fat_calories / calculated_total) * 100
    else:
        protein_percent = carbs_percent = fat_percent = 0
    
    return {
        "date": target_date.strftime('%Y-%m-%d'),
        "total_calories": total_calories,
        "macros": {
            "protein": {
                "grams": round(total_protein, 1),
                "calories": round(protein_calories, 1),
                "percent": round(protein_percent, 1)
            },
            "carbs": {
                "grams": round(total_carbs, 1),
                "calories": round(carbs_calories, 1),
                "percent": round(carbs_percent, 1)
            },
            "fat": {
                "grams": round(total_fat, 1),
                "calories": round(fat_calories, 1),
                "percent": round(fat_percent, 1)
            }
        }
    }


# ==========================================
# CALORIE COMPARISON (Target vs Actual)
# ==========================================

def get_calorie_comparison(
    db: Session,
    user_id: UUID,
    start_date: date,
    end_date: date
) -> Dict:
    """
    Compare actual calories vs target over date range
    """
    
    # Get user's active goal
    goal = db.query(UserGoal).filter(
        UserGoal.user_id == user_id,
        UserGoal.is_active == True
    ).first()
    
    if not goal or not goal.daily_calorie_target:
        return {
            "error": "No active goal with calorie target found",
            "comparison": []
        }
    
    target_calories = goal.daily_calorie_target
    
    # Get daily actual calories
    results = db.query(
        FoodLog.meal_date,
        func.sum(FoodLog.calories).label('actual_calories')
    ).filter(
        FoodLog.user_id == user_id,
        FoodLog.meal_date >= start_date,
        FoodLog.meal_date <= end_date
    ).group_by(FoodLog.meal_date).order_by(FoodLog.meal_date).all()
    
    comparison = []
    for row in results:
        actual = float(row.actual_calories or 0)
        difference = actual - target_calories
        percentage = (actual / target_calories * 100) if target_calories > 0 else 0
        
        comparison.append({
            "date": row.meal_date.strftime('%Y-%m-%d'),
            "target_calories": target_calories,
            "actual_calories": round(actual, 1),
            "difference": round(difference, 1),
            "percentage": round(percentage, 1),
            "status": "over" if difference > 0 else "under" if difference < -100 else "on_track"
        })
    
    # Calculate summary
    avg_actual = sum(c['actual_calories'] for c in comparison) / len(comparison) if comparison else 0
    days_on_track = sum(1 for c in comparison if c['status'] == 'on_track')
    
    return {
        "target_calories": target_calories,
        "average_actual": round(avg_actual, 1),
        "days_tracked": len(comparison),
        "days_on_track": days_on_track,
        "adherence_rate": round((days_on_track / len(comparison) * 100), 1) if comparison else 0,
        "comparison": comparison
    }


# ==========================================
# MEAL PATTERNS
# ==========================================

def get_meal_patterns(
    db: Session,
    user_id: UUID,
    days: int = 30
) -> Dict:
    """
    Analyze meal timing patterns (which meals user logs most)
    """
    
    cutoff_date = date.today() - timedelta(days=days)
    
    # Get meal type distribution
    results = db.query(
        FoodLog.meal_type,
        func.count(FoodLog.log_id).label('count'),
        func.avg(FoodLog.calories).label('avg_calories')
    ).filter(
        FoodLog.user_id == user_id,
        FoodLog.meal_date >= cutoff_date
    ).group_by(FoodLog.meal_type).all()
    
    patterns = {}
    total_meals = 0
    
    for row in results:
        count = row.count
        total_meals += count
        patterns[row.meal_type] = {
            "count": count,
            "avg_calories": round(float(row.avg_calories or 0), 1),
            "percentage": 0  # Will calculate after
        }
    
    # Calculate percentages
    for meal_type in patterns:
        patterns[meal_type]['percentage'] = round(
            (patterns[meal_type]['count'] / total_meals * 100), 1
        ) if total_meals > 0 else 0
    
    return {
        "days_analyzed": days,
        "total_meals": total_meals,
        "patterns": patterns,
        "most_common_meal": max(patterns.items(), key=lambda x: x[1]['count'])[0] if patterns else None
    }


# ==========================================
# GOAL PROGRESS
# ==========================================

def get_goal_progress(
    db: Session,
    user_id: UUID
) -> Dict:
    """
    Get current progress towards active goal
    """
    
    # Get active goal
    goal = db.query(UserGoal).filter(
        UserGoal.user_id == user_id,
        UserGoal.is_active == True
    ).first()
    
    if not goal:
        return {"error": "No active goal found"}
    
    # Get current weight
    latest_weight = db.query(WeightLog).filter(
        WeightLog.user_id == user_id
    ).order_by(WeightLog.measured_date.desc()).first()
    
    current_weight = float(latest_weight.weight_kg) if latest_weight else float(goal.current_weight_kg)
    starting_weight = float(goal.current_weight_kg)
    target_weight = float(goal.target_weight_kg) if goal.target_weight_kg else None
    
    # Calculate progress
    if target_weight:
        total_change_needed = target_weight - starting_weight
        actual_change = current_weight - starting_weight
        
        if total_change_needed != 0:
            progress_percent = (actual_change / total_change_needed) * 100
        else:
            progress_percent = 100 if abs(current_weight - target_weight) < 0.5 else 0
        
        remaining = target_weight - current_weight
    else:
        progress_percent = 0
        remaining = 0
    
    # Days tracking
    # Convert dates to date object if they're datetime
    goal_created_at = goal.created_at.date() if hasattr(goal.created_at, 'date') else goal.created_at
    goal_target_date = goal.target_date.date() if goal.target_date and hasattr(goal.target_date, 'date') else goal.target_date
    
    days_elapsed = (date.today() - goal_created_at).days
    days_to_target = (goal_target_date - date.today()).days if goal_target_date else None
    
    return {
        "goal_type": goal.goal_type,
        "starting_weight": starting_weight,
        "current_weight": current_weight,
        "target_weight": target_weight,
        "weight_change": round(current_weight - starting_weight, 2),
        "remaining": round(remaining, 2) if target_weight else None,
        "progress_percent": round(progress_percent, 1),
        "days_elapsed": days_elapsed,
        "days_to_target": days_to_target,
        "target_date": goal.target_date.strftime('%Y-%m-%d') if goal.target_date else None,
        "daily_calorie_target": goal.daily_calorie_target,
        "status": "on_track" if progress_percent >= 0 else "behind"
    }


# ==========================================
# FOOD FREQUENCY
# ==========================================

def get_food_frequency(
    db: Session,
    user_id: UUID,
    days: int = 30,
    limit: int = 10
) -> List[Dict]:
    """
    Get most frequently logged foods
    """
    
    cutoff_date = date.today() - timedelta(days=days)
    
    results = db.query(
        FoodLog.food_name,
        func.count(FoodLog.log_id).label('count'),
        func.sum(FoodLog.calories).label('total_calories'),
        func.avg(FoodLog.calories).label('avg_calories')
    ).filter(
        FoodLog.user_id == user_id,
        FoodLog.meal_date >= cutoff_date
    ).group_by(FoodLog.food_name).order_by(
        func.count(FoodLog.log_id).desc()
    ).limit(limit).all()
    
    frequency = []
    for row in results:
        frequency.append({
            "food_name": row.food_name,
            "times_logged": row.count,
            "total_calories": round(float(row.total_calories or 0), 1),
            "avg_calories_per_serving": round(float(row.avg_calories or 0), 1)
        })
    
    return frequency


# ==========================================
# DAILY REMAINING NUTRIENTS (NEW - for Module 3)
# ==========================================

def get_daily_remaining_nutrients(
    db: Session,
    user_id: UUID,
    target_date: Optional[date] = None
) -> Dict:
    """
    Get remaining nutrients for a specific date
    
    This function wraps NutritionCalculatorCore for analytics/reporting purposes.
    For Module 3 (Recommendations), use NutritionCalculatorCore directly.
    
    Args:
        db: Database session
        user_id: User UUID
        target_date: Date to calculate for (default: today)
    
    Returns:
        {
            "date": "2026-02-22",
            "goal": {
                "daily_calorie_target": 2000,
                "target_protein": 120,
                "target_carbs": 225,
                "target_fat": 67
            },
            "consumed": {
                "calories": 1200,
                "protein": 65,
                "carbs": 140,
                "fat": 38
            },
            "remaining": {
                "calories": 800,
                "protein": 55,
                "carbs": 85,
                "fat": 29
            },
            "progress_percent": {
                "calories": 60.0,
                "protein": 54.2,
                "carbs": 62.2,
                "fat": 56.7
            }
        }
    
    Raises:
        ValueError: If user has no active goal
    
    Example:
        >>> remaining = get_daily_remaining_nutrients(db, user_id)
        >>> print(f"Còn thiếu {remaining['remaining']['calories']} calories")
    """
    
    from app.services.nutrition_calculator import NutritionCalculatorCore
    
    target_date = target_date or datetime.now().date()
    
    # Get user's active goal
    goal = db.query(UserGoal).filter(
        UserGoal.user_id == user_id,
        UserGoal.is_active == True,
        UserGoal.is_deleted == False
    ).first()
    
    if not goal:
        raise ValueError("User must have an active goal to calculate remaining nutrients")
    
    if not goal.daily_calorie_target:
        raise ValueError("Goal must have daily_calorie_target set")
    
    # Get consumed nutrients
    consumed = db.query(
        func.coalesce(func.sum(FoodLog.calories), 0).label('calories'),
        func.coalesce(func.sum(FoodLog.protein_g), 0).label('protein'),
        func.coalesce(func.sum(FoodLog.carbs_g), 0).label('carbs'),
        func.coalesce(func.sum(FoodLog.fat_g), 0).label('fat')
    ).filter(
        FoodLog.user_id == user_id,
        FoodLog.meal_date == target_date,
        FoodLog.is_deleted == False
    ).first()
    
    # Calculate remaining
    calculator = NutritionCalculatorCore(db)
    remaining = calculator.calculate_daily_remaining(user_id, target_date)
    
    # Calculate progress percentages
    goal_cal = float(goal.daily_calorie_target)
    goal_protein = float(goal.protein_target_g or 0)
    goal_carbs = float(goal.carbs_target_g or 0)
    goal_fat = float(goal.fat_target_g or 0)
    
    consumed_cal = float(consumed.calories or 0)
    consumed_protein = float(consumed.protein or 0)
    consumed_carbs = float(consumed.carbs or 0)
    consumed_fat = float(consumed.fat or 0)
    
    progress = {
        "calories": round((consumed_cal / goal_cal * 100), 1) if goal_cal > 0 else 0,
        "protein": round((consumed_protein / goal_protein * 100), 1) if goal_protein > 0 else 0,
        "carbs": round((consumed_carbs / goal_carbs * 100), 1) if goal_carbs > 0 else 0,
        "fat": round((consumed_fat / goal_fat * 100), 1) if goal_fat > 0 else 0,
    }
    
    return {
        "date": target_date.strftime('%Y-%m-%d'),
        "goal": {
            "daily_calorie_target": goal_cal,
            "target_protein": goal_protein,
            "target_carbs": goal_carbs,
            "target_fat": goal_fat
        },
        "consumed": {
            "calories": round(consumed_cal, 1),
            "protein": round(consumed_protein, 1),
            "carbs": round(consumed_carbs, 1),
            "fat": round(consumed_fat, 1)
        },
        "remaining": {
            "calories": round(remaining["calories"], 1),
            "protein": round(remaining["protein"], 1),
            "carbs": round(remaining["carbs"], 1),
            "fat": round(remaining["fat"], 1)
        },
        "progress_percent": progress
    }