"""
Meal Plan Schemas
"""

from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, List, Dict
from datetime import date, datetime, timedelta
from uuid import UUID
from decimal import Decimal

class MealPlanItemCreate(BaseModel):
    """Schema cho việc thêm món ăn vào kế hoạch"""
    food_id: Optional[UUID] = None  # Chuyển thành Optional vì có thể là Recipe
    day_date: date
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack)$")
    serving_size_g: Decimal = Field(default=Decimal("100.0"), gt=0)
    quantity: Decimal = Field(default=Decimal("1.0"), gt=0)
    unit: str = "serving"
    notes: Optional[str] = None
    order_index: Optional[int] = Field(0, ge=0)
    # Thêm các trường này để nhận dữ liệu snapshot nếu cần
    calories: Optional[Decimal] = None
    protein_g: Optional[Decimal] = None
    carbs_g: Optional[Decimal] = None
    fat_g: Optional[Decimal] = None

class MealPlanItemResponse(BaseModel):
    """Schema phản hồi thông tin bữa ăn (đã lưu snapshot)"""
    item_id: UUID
    meal_plan_id: UUID
    food_id: Optional[UUID]  # Có thể là None nếu là món ăn từ Recipe
    day_date: date
    meal_type: str
    serving_size_g: Decimal
    quantity: Decimal
    unit: str
    calories: Optional[Decimal]
    protein_g: Optional[Decimal]
    carbs_g: Optional[Decimal]
    fat_g: Optional[Decimal]
    notes: Optional[str]
    order_index: Optional[int]
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_serializer("serving_size_g", "quantity", "calories", "protein_g", "carbs_g", "fat_g")
    def serialize_decimal(self, value: Decimal, _info):
        return float(value) if value is not None else 0.0

class MealPlanCreate(BaseModel):
    """Schema for creating meal plan"""
    plan_name: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)
    servings: int = Field(default=1, ge=1)
    difficulty_level: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    preferences: Optional[dict] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plan_name": "Healthy Week Plan",
                "start_date": "2024-12-27",
                "end_date": "2025-01-03",
                "servings": 1,
                "difficulty_level": "easy"
            }
        }
    )

class MealPlanResponse(BaseModel):
    """Schema for meal plan response"""
    plan_id: UUID
    user_id: UUID
    plan_name: str
    start_date: date
    end_date: date
    prep_time_minutes: Optional[int]
    cook_time_minutes: Optional[int]
    servings: int
    difficulty_level: Optional[str]
    preferences: dict
    is_active: bool
    is_completed: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MealPlanWithItems(MealPlanResponse):
    """Schema for meal plan with items"""
    items: List[MealPlanItemResponse] = []


class MealPlanItemSimple(BaseModel):
    """Simplified item schema for days view"""
    item_id: UUID
    meal_type: str
    serving_size_g: Decimal
    quantity: Decimal
    unit: str
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    notes: Optional[str] = None
    recipe_name: Optional[str] = None
    food_name: Optional[str] = None

    @classmethod
    def from_item(cls, item: "MealPlanItem") -> "MealPlanItemSimple":
        """Convert from SQLAlchemy model"""
        name = None
        # Handle both "Recipe: " (from database) and "Custom: " (from AI)
        if item.notes:
            if item.notes.startswith("Recipe: "):
                name = item.notes.replace("Recipe: ", "")
            elif item.notes.startswith("Custom: "):
                # Extract food name from "Custom: {name} | Nguyên liệu: ..."
                custom_part = item.notes.replace("Custom: ", "")
                pipe_index = custom_part.find(" | ")
                if pipe_index > 0:
                    name = custom_part[:pipe_index]
                else:
                    name = custom_part
        return cls(
            item_id=item.item_id,
            meal_type=item.meal_type,
            serving_size_g=float(item.serving_size_g) if item.serving_size_g else 100,
            quantity=float(item.quantity) if item.quantity else 1,
            unit=item.unit or "serving",
            calories=float(item.calories) if item.calories else None,
            protein_g=float(item.protein_g) if item.protein_g else None,
            carbs_g=float(item.carbs_g) if item.carbs_g else None,
            fat_g=float(item.fat_g) if item.fat_g else None,
            notes=item.notes,
            recipe_name=name,
        )


class MealPlanDayResponse(BaseModel):
    """Schema for a single day in meal plan"""
    day_number: int
    date: str
    items: List[MealPlanItemSimple]
    total_calories: float


class MealPlanWithDays(BaseModel):
    """Schema for meal plan with days grouped (used by frontend)"""
    plan_id: UUID
    user_id: UUID
    plan_name: str
    start_date: date
    end_date: date
    prep_time_minutes: Optional[int]
    cook_time_minutes: Optional[int]
    servings: int
    difficulty_level: Optional[str]
    preferences: dict
    is_active: bool
    is_completed: bool
    created_at: datetime
    total_calories: float = 0
    days: List[MealPlanDayResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_meal_plan(cls, plan: "MealPlan") -> "MealPlanWithDays":
        """Convert from SQLAlchemy MealPlan + items to days grouped format"""
        from collections import defaultdict

        items = plan.items if hasattr(plan, 'items') and plan.items else []

        # Group items by date
        by_date: Dict[str, List] = defaultdict(list)
        for item in items:
            date_key = str(item.day_date) if item.day_date else ""
            by_date[date_key].append(item)

        # Calculate total calories
        total_cal = sum(float(i.calories or 0) for i in items)

        # Build days list
        start = plan.start_date
        end = plan.end_date
        days_list = []
        day_num = 1

        current = start
        while current <= end:
            date_str = str(current)
            day_items = by_date.get(date_str, [])
            day_calories = sum(float(i.calories or 0) for i in day_items)

            days_list.append(MealPlanDayResponse(
                day_number=day_num,
                date=date_str,
                items=[MealPlanItemSimple.from_item(i) for i in day_items],
                total_calories=day_calories
            ))
            current += timedelta(days=1)
            day_num += 1

        return cls(
            plan_id=plan.plan_id,
            user_id=plan.user_id,
            plan_name=plan.plan_name,
            start_date=plan.start_date,
            end_date=plan.end_date,
            prep_time_minutes=plan.prep_time_minutes,
            cook_time_minutes=plan.cook_time_minutes,
            servings=plan.servings,
            difficulty_level=plan.difficulty_level,
            preferences=plan.preferences or {},
            is_active=plan.is_active,
            is_completed=plan.is_completed,
            created_at=plan.created_at,
            total_calories=total_cal,
            days=days_list
        )


class MealPlanUpdate(BaseModel):
    """Schema for updating meal plan (partial update)"""
    plan_name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(None, pattern="^(active|completed|archived)$")
    preferences: Optional[dict] = None
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "plan_name": "Updated Plan Name",
            "status": "completed"
        }
    })