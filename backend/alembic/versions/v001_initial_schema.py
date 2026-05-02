"""v001_initial_schema - Create all base tables

Revision ID: v001
Revises:
Create Date: 2026-04-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = 'v001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================
    # 1. USERS TABLE
    # ==========================================
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'),
                  comment='Unique user identifier'),
        sa.Column('email', sa.String(255), unique=True, nullable=False,
                  comment='User email address'),
        sa.Column('password_hash', sa.String(255), nullable=False,
                  comment='Hashed password (bcrypt)'),
        sa.Column('full_name', sa.String(255), nullable=True,
                  comment='User full name'),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False, index=True,
                  comment='Account active status'),
        sa.Column('is_admin', sa.Boolean, default=False, nullable=False,
                  comment='Admin privileges'),
        sa.Column('email_verified', sa.Boolean, default=False, nullable=False,
                  comment='Email verification status'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True,
                  comment='Last login timestamp'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()'),
                  comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()'),
                  comment='Record last update timestamp'),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False,
                  server_default=sa.text('false'),
                  comment='Trạng thái xóa (False=Active, True=Deleted)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Soft delete timestamp'),
        sa.CheckConstraint("email LIKE '%@%.%'", name='basic_email_format'),
    )
    op.create_index('ix_users_is_deleted', 'users', ['is_deleted'])

    # ==========================================
    # 2. USER PROFILES TABLE
    # ==========================================
    op.create_table(
        'user_profiles',
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.user_id', ondelete='CASCADE'),
                  unique=True, nullable=False),
        sa.Column('date_of_birth', sa.Date, nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('height_cm', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('activity_level', sa.String(50), nullable=True),
        sa.Column('profile_image_url', sa.String, nullable=True),
        sa.Column('timezone', sa.String(50), default='Asia/Ho_Chi_Minh'),
        sa.Column('language', sa.String(10), default='vi'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False,
                  server_default=sa.text('false'),
                  comment='Trạng thái xóa (False=Active, True=Deleted)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "gender IN ('male', 'female', 'other')",
            name='valid_gender'
        ),
        sa.CheckConstraint(
            "height_cm BETWEEN 50 AND 300",
            name='valid_height'
        ),
        sa.CheckConstraint(
            "activity_level IN ('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extra_active')",
            name='valid_activity_level'
        ),
    )
    op.create_index('ix_user_profiles_is_deleted', 'user_profiles', ['is_deleted'])

    # ==========================================
    # 3. USER GOALS TABLE
    # ==========================================
    op.create_table(
        'user_goals',
        sa.Column('goal_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.user_id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('goal_type', sa.String(50), nullable=False),
        sa.Column('current_weight_kg', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('target_weight_kg', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('target_date', sa.Date, nullable=True),
        sa.Column('daily_calorie_target', sa.Integer, nullable=True),
        sa.Column('protein_target_g', sa.Integer, nullable=True),
        sa.Column('carbs_target_g', sa.Integer, nullable=True),
        sa.Column('fat_target_g', sa.Integer, nullable=True),
        sa.Column('health_conditions', postgresql.ARRAY(sa.String), default=list),
        sa.Column('food_allergies', postgresql.ARRAY(sa.String), default=list),
        sa.Column('dietary_preferences', postgresql.ARRAY(sa.String), default=list),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False,
                  server_default=sa.text('false'),
                  comment='Trạng thái xóa (False=Active, True=Deleted)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "goal_type IN ('weight_loss', 'weight_gain', 'maintain', 'healthy_lifestyle')",
            name='valid_goal_type'
        ),
        sa.CheckConstraint('current_weight_kg > 0', name='valid_current_weight'),
        sa.CheckConstraint('target_weight_kg > 0', name='valid_target_weight'),
        sa.CheckConstraint('daily_calorie_target > 0', name='valid_calorie_target'),
        # Note: one_active_goal_per_user_idx is created after table creation below
    )
    op.create_index('ix_user_goals_is_deleted', 'user_goals', ['is_deleted'])
    # Note: ix_user_goals_user_id is auto-created by FK constraint on user_id (index=True)
    # Partial unique index for one active goal per user
    op.create_index(
        'one_active_goal_per_user_idx', 'user_goals', ['user_id'],
        unique=True,
        postgresql_where=sa.text('is_active IS TRUE AND is_deleted IS FALSE')
    )

    # ==========================================
    # 4. FOODS TABLE
    # NOTE: Skipped - table already created by seed script
    # Soft delete columns will be added by migration 954b5611f119
    # ==========================================
    # op.create_table(...)  # SKIPPED

    # ==========================================
    # 4b. FOOD SERVINGS TABLE
    # NOTE: Skipped - table already created by seed script
    # Soft delete columns will be added by migration 954b5611f119
    # ==========================================
    # op.create_table(...)  # SKIPPED

    # ==========================================
    # 5. FOOD LOGS TABLE
    # ==========================================
    op.create_table(
        'food_logs',
        sa.Column('log_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.user_id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('food_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('foods.food_id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('food_name', sa.String(255), nullable=False),
        sa.Column('serving_size_g', sa.DECIMAL(8, 2), nullable=False),
        sa.Column('quantity', sa.DECIMAL(8, 2), default=1.0, nullable=False),
        sa.Column('calories', sa.DECIMAL(8, 2), nullable=False),
        sa.Column('protein_g', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('carbs_g', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('fat_g', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('meal_type', sa.String(50), nullable=False),
        sa.Column('meal_date', sa.Date, nullable=False, index=True),
        sa.Column('meal_time', sa.Time, nullable=True),
        sa.Column('image_url', sa.Text, nullable=True),
        sa.Column('was_ai_recognized', sa.Boolean, default=False, nullable=False),
        sa.Column('ai_confidence', sa.DECIMAL(5, 4), nullable=True),
        sa.Column('ai_prediction_correct', sa.Boolean, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('serving_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False,
                  server_default=sa.text('false'),
                  comment='Trạng thái xóa (False=Active, True=Deleted)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name='valid_meal_type'
        ),
        sa.CheckConstraint('quantity > 0', name='valid_quantity'),
        sa.CheckConstraint('serving_size_g > 0', name='valid_serving_size'),
        sa.CheckConstraint('calories >= 0', name='valid_calories'),
        sa.CheckConstraint(
            'ai_confidence IS NULL OR ai_confidence BETWEEN 0 AND 1',
            name='valid_ai_confidence'
        ),
    )
    op.create_index('ix_food_logs_is_deleted', 'food_logs', ['is_deleted'])
    op.create_index('idx_foodlog_user_date', 'food_logs', ['user_id', 'meal_date'])
    op.create_index('idx_foodlog_user_meal_date', 'food_logs',
                    ['user_id', 'meal_type', 'meal_date'])
    op.create_index('idx_foodlog_ai', 'food_logs', ['was_ai_recognized', 'created_at'])

    # ==========================================
    # 6. WEIGHT LOGS TABLE
    # ==========================================
    op.create_table(
        'weight_logs',
        sa.Column('weight_log_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.user_id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('weight_kg', sa.DECIMAL(5, 2), nullable=False),
        sa.Column('measured_date', sa.Date, nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False,
                  server_default=sa.text('false'),
                  comment='Trạng thái xóa (False=Active, True=Deleted)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('weight_kg BETWEEN 20 AND 300', name='valid_weight'),
    )
    op.create_index('ix_weight_logs_is_deleted', 'weight_logs', ['is_deleted'])
    op.create_index('idx_weight_logs_user_date', 'weight_logs',
                    ['user_id', 'measured_date'], unique=True)

    # ==========================================
    # 7. RECIPES TABLE
    # ==========================================
    op.create_table(
        'recipes',
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name_vi', sa.String(255), nullable=False, index=True),
        sa.Column('name_en', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=False, index=True),
        sa.Column('cuisine_type', sa.String(50), nullable=True),
        sa.Column('prep_time_minutes', sa.Integer, nullable=True),
        sa.Column('cook_time_minutes', sa.Integer, nullable=True),
        sa.Column('servings', sa.Integer, default=1, nullable=False),
        sa.Column('difficulty_level', sa.String(50), nullable=True),
        sa.Column('instructions', sa.Text, nullable=True),
        sa.Column('instructions_steps', postgresql.JSONB, nullable=True),
        sa.Column('calories_per_serving', sa.DECIMAL(8, 2), nullable=True),
        sa.Column('protein_per_serving', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('carbs_per_serving', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('fat_per_serving', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('fiber_per_serving', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('image_url', sa.Text, nullable=True),
        sa.Column('video_url', sa.Text, nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('is_verified', sa.Boolean, default=False, nullable=False, index=True),
        sa.Column('is_public', sa.Boolean, default=True, nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.user_id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String), default=list),
        sa.Column('view_count', sa.Integer, default=0, nullable=False),
        sa.Column('favorite_count', sa.Integer, default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False,
                  server_default=sa.text('false'),
                  comment='Trạng thái xóa (False=Active, True=Deleted)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('prep_time_minutes >= 0', name='valid_prep_time'),
        sa.CheckConstraint('cook_time_minutes >= 0', name='valid_cook_time'),
        sa.CheckConstraint('servings > 0', name='valid_servings'),
        sa.CheckConstraint(
            "difficulty_level IN ('easy', 'medium', 'hard')",
            name='valid_difficulty'
        ),
        sa.CheckConstraint('calories_per_serving >= 0', name='valid_recipe_calories'),
    )
    op.create_index('ix_recipes_is_deleted', 'recipes', ['is_deleted'])
    op.create_index('idx_recipe_category_verified', 'recipes', ['category', 'is_verified'])
    op.create_index('idx_recipe_created_by', 'recipes', ['created_by'])

    # ==========================================
    # 8. RECIPE INGREDIENTS TABLE
    # ==========================================
    op.create_table(
        'recipe_ingredients',
        sa.Column('ingredient_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('recipes.recipe_id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('food_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('foods.food_id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('ingredient_name', sa.String(255), nullable=False),
        sa.Column('quantity', sa.DECIMAL(8, 2), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('order_index', sa.Integer, default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False,
                  server_default=sa.text('false'),
                  comment='Trạng thái xóa (False=Active, True=Deleted)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('quantity > 0', name='valid_ingredient_quantity'),
    )
    op.create_index('ix_recipe_ingredients_is_deleted', 'recipe_ingredients', ['is_deleted'])

    # ==========================================
    # 9. RECIPE FAVORITES TABLE
    # ==========================================
    op.create_table(
        'recipe_favorites',
        sa.Column('favorite_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.user_id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('recipes.recipe_id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False,
                  server_default=sa.text('false'),
                  comment='Trạng thái xóa (False=Active, True=Deleted)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_recipe_favorites_is_deleted', 'recipe_favorites', ['is_deleted'])
    op.create_index('idx_user_recipe_unique', 'recipe_favorites',
                    ['user_id', 'recipe_id'], unique=True)

    # ==========================================
    # 10. MEAL PLANS TABLE
    # ==========================================
    op.create_table(
        'meal_plans',
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.user_id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('plan_name', sa.String(255), nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('prep_time_minutes', sa.Integer, nullable=True),
        sa.Column('cook_time_minutes', sa.Integer, nullable=True),
        sa.Column('servings', sa.Integer, default=1, nullable=False),
        sa.Column('difficulty_level', sa.String(50), nullable=True),
        sa.Column('preferences', postgresql.JSONB, default={}, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False, index=True),
        sa.Column('is_completed', sa.Boolean, default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False,
                  server_default=sa.text('false'),
                  comment='Trạng thái xóa (False=Active, True=Deleted)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('end_date >= start_date', name='valid_date_range'),
        sa.CheckConstraint('prep_time_minutes >= 0', name='valid_meal_plan_prep_time'),
        sa.CheckConstraint('cook_time_minutes >= 0', name='valid_meal_plan_cook_time'),
        sa.CheckConstraint('servings > 0', name='valid_meal_plan_servings'),
        sa.CheckConstraint(
            "difficulty_level IN ('easy', 'medium', 'hard')",
            name='valid_meal_plan_difficulty'
        ),
    )
    op.create_index('ix_meal_plans_is_deleted', 'meal_plans', ['is_deleted'])
    # Note: ix_meal_plans_user_id is auto-created by FK constraint on user_id (index=True)

    # ==========================================
    # 11. MEAL PLAN ITEMS TABLE
    # ==========================================
    op.create_table(
        'meal_plan_items',
        sa.Column('item_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('meal_plan_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('meal_plans.plan_id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('food_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('foods.food_id', ondelete='CASCADE'),
                  nullable=True),
        sa.Column('day_date', sa.Date, nullable=False, index=True),
        sa.Column('meal_type', sa.String(50), nullable=False),
        sa.Column('serving_size_g', sa.DECIMAL(8, 2), nullable=False),
        sa.Column('quantity', sa.DECIMAL(8, 2), default=1.0, nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('calories', sa.DECIMAL(8, 2), nullable=True),
        sa.Column('protein_g', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('carbs_g', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('fat_g', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('order_index', sa.Integer, default=0, nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean, default=False, nullable=False,
                  server_default=sa.text('false'),
                  comment='Trạng thái xóa (False=Active, True=Deleted)'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name='valid_meal_plan_item_meal_type'
        ),
        sa.CheckConstraint('calories >= 0', name='valid_meal_plan_item_calories'),
        sa.CheckConstraint('order_index >= 0', name='valid_order_index'),
        sa.CheckConstraint('quantity > 0', name='valid_meal_plan_item_quantity'),
        sa.CheckConstraint('serving_size_g > 0', name='valid_meal_plan_item_serving_size'),
    )
    op.create_index('ix_meal_plan_items_is_deleted', 'meal_plan_items', ['is_deleted'])
    # Note: ix_meal_plan_items_meal_plan_id is auto-created by FK constraint (index=True)
    op.create_index('ix_meal_plan_items_day_date', 'meal_plan_items', ['day_date'])

    # ==========================================
    # 12. PORTION PRESETS TABLE
    # ==========================================
    op.create_table(
        'portion_presets',
        sa.Column('preset_id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('food_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('foods.food_id', ondelete='CASCADE'),
                  nullable=True, index=True),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('recipes.recipe_id', ondelete='CASCADE'),
                  nullable=True, index=True),
        sa.Column('size_label', sa.String(50), nullable=False),
        sa.Column('display_name_vi', sa.String(100), nullable=False),
        sa.Column('display_name_en', sa.String(100), nullable=True),
        sa.Column('unit_type', sa.String(30), nullable=False),
        sa.Column('unit_display_vi', sa.String(50), nullable=False),
        sa.Column('unit_display_en', sa.String(50), nullable=True),
        sa.Column('grams', sa.Integer, nullable=False),
        sa.Column('is_default', sa.Boolean, default=False, nullable=False, index=True),
        sa.Column('sort_order', sa.Integer, default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        # PortionPreset does NOT use SoftDeleteMixin per model definition
        sa.CheckConstraint('grams > 0', name='positive_grams'),
        sa.CheckConstraint(
            "(food_id IS NOT NULL AND recipe_id IS NULL) OR (food_id IS NULL AND recipe_id IS NOT NULL)",
            name='check_food_or_recipe_not_both'
        ),
    )
    op.create_index(
        'uq_portion_preset_item_size', 'portion_presets',
        ['food_id', 'recipe_id', 'size_label'], unique=True
    )


def downgrade() -> None:
    op.drop_table('portion_presets')
    op.drop_table('meal_plan_items')
    op.drop_table('meal_plans')
    op.drop_table('recipe_favorites')
    op.drop_table('recipe_ingredients')
    op.drop_table('recipes')
    op.drop_table('weight_logs')
    op.drop_table('food_logs')
    op.drop_table('foods')
    op.drop_table('user_goals')
    op.drop_table('user_profiles')
    op.drop_table('users')
