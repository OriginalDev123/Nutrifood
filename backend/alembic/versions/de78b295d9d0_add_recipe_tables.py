"""add_recipe_tables

Revision ID: de78b295d9d0
Revises: de1d1b920b60
Create Date: 2026-01-07 17:08:56.507203

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de78b295d9d0'
down_revision: Union[str, None] = 'de1d1b920b60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ==========================================
    # CREATE RECIPES TABLE
    # ==========================================
    op.create_table(
        'recipes',
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name_vi', sa.String(255), nullable=False),
        sa.Column('name_en', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('cuisine_type', sa.String(50), nullable=True),
        
        sa.Column('prep_time_minutes', sa.Integer, nullable=True),
        sa.Column('cook_time_minutes', sa.Integer, nullable=True),
        sa.Column('servings', sa.Integer, nullable=False, server_default='1'),
        sa.Column('difficulty_level', sa.String(50), nullable=True),
        
        sa.Column('instructions', sa.Text, nullable=True),
        sa.Column('instructions_steps', postgresql.ARRAY(sa.Text), nullable=True),
        
        sa.Column('calories_per_serving', sa.DECIMAL(8, 2), nullable=True),
        sa.Column('protein_per_serving', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('carbs_per_serving', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('fat_per_serving', sa.DECIMAL(6, 2), nullable=True),
        sa.Column('fiber_per_serving', sa.DECIMAL(6, 2), nullable=True),
        
        sa.Column('image_url', sa.Text, nullable=True),
        sa.Column('video_url', sa.Text, nullable=True),
        
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String), nullable=True),
        
        sa.Column('view_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('favorite_count', sa.Integer, nullable=False, server_default='0'),
        
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        
        sa.CheckConstraint('prep_time_minutes >= 0', name='valid_prep_time'),
        sa.CheckConstraint('cook_time_minutes >= 0', name='valid_cook_time'),
        sa.CheckConstraint('servings > 0', name='valid_servings'),
        sa.CheckConstraint("difficulty_level IN ('easy', 'medium', 'hard')", name='valid_difficulty'),
        sa.CheckConstraint('calories_per_serving >= 0', name='valid_recipe_calories')
    )
    
    # Create indexes for recipes
    op.create_index('idx_recipes_name_vi', 'recipes', ['name_vi'])
    op.create_index('idx_recipes_category', 'recipes', ['category'])
    op.create_index('idx_recipes_is_verified', 'recipes', ['is_verified'])
    op.create_index('idx_recipe_category_verified', 'recipes', ['category', 'is_verified'])
    op.create_index('idx_recipes_created_by', 'recipes', ['created_by'])
    
    # ==========================================
    # CREATE RECIPE_INGREDIENTS TABLE
    # ==========================================
    op.create_table(
        'recipe_ingredients',
        sa.Column('ingredient_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recipes.recipe_id', ondelete='CASCADE'), nullable=False),
        sa.Column('food_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('foods.food_id', ondelete='SET NULL'), nullable=True),
        sa.Column('ingredient_name', sa.String(255), nullable=False),
        sa.Column('quantity', sa.DECIMAL(8, 2), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('order_index', sa.Integer, nullable=False, server_default='0'),
        
        sa.CheckConstraint('quantity > 0', name='valid_ingredient_quantity')
    )
    
    op.create_index('idx_recipe_ingredients_recipe_id', 'recipe_ingredients', ['recipe_id'])
    
    # ==========================================
    # CREATE RECIPE_FAVORITES TABLE
    # ==========================================
    op.create_table(
        'recipe_favorites',
        sa.Column('favorite_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recipes.recipe_id', ondelete='CASCADE'), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    
    op.create_index('idx_recipe_favorites_user_id', 'recipe_favorites', ['user_id'])
    op.create_index('idx_recipe_favorites_recipe_id', 'recipe_favorites', ['recipe_id'])
    op.create_index('idx_user_recipe_unique', 'recipe_favorites', ['user_id', 'recipe_id'], unique=True)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('recipe_favorites')
    op.drop_table('recipe_ingredients')
    op.drop_table('recipes')