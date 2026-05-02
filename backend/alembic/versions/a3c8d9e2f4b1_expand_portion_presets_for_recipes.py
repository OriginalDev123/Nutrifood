"""expand_portion_presets_for_recipes

Revision ID: a3c8d9e2f4b1
Revises: f1a2b3c4d5e6
Create Date: 2026-03-02 14:30:00.000000

Changes:
- Make food_id nullable
- Add recipe_id column with FK to recipes
- Add CHECK constraint: only one of food_id or recipe_id must be set
- Update unique constraint to include recipe_id
- Add index on recipe_id

This allows portion_presets to work with both foods (raw ingredients) 
and recipes (prepared dishes).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'a3c8d9e2f4b1'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    """
    Expand portion_presets to support both foods and recipes
    
    Priority: Recipes (món ăn) > Foods (nguyên liệu)
    Use cases:
    - Vision AI detects "Phở bò" → recipe portion presets
    - "What can I cook?" feature → food portion presets
    """
    
    # ==========================================
    # STEP 1: DROP EXISTING CONSTRAINTS
    # ==========================================
    
    # Drop unique constraint (need to recreate with recipe_id)
    op.drop_constraint('unique_food_size', 'portion_presets', type_='unique')
    
    # ==========================================
    # STEP 2: MODIFY EXISTING COLUMNS
    # ==========================================
    
    # Make food_id nullable (was NOT NULL)
    op.alter_column('portion_presets', 'food_id',
                    existing_type=UUID(),
                    nullable=True)
    
    # ==========================================
    # STEP 3: ADD NEW COLUMNS
    # ==========================================
    
    # Add recipe_id column
    op.add_column('portion_presets',
                  sa.Column('recipe_id', UUID(), nullable=True))
    
    # ==========================================
    # STEP 4: ADD CONSTRAINTS
    # ==========================================
    
    # CHECK: Only one of food_id or recipe_id can be set (XOR logic)
    op.create_check_constraint(
        'check_food_or_recipe_not_both',
        'portion_presets',
        '(food_id IS NOT NULL AND recipe_id IS NULL) OR (food_id IS NULL AND recipe_id IS NOT NULL)'
    )
    
    # Updated UNIQUE constraint: Include recipe_id in combination
    # This ensures unique presets for each food/recipe + size combination
    op.create_unique_constraint(
        'uq_portion_preset_item_size',
        'portion_presets',
        ['food_id', 'recipe_id', 'size_label']
    )
    
    # ==========================================
    # STEP 5: ADD FOREIGN KEY
    # ==========================================
    
    # Foreign key: recipe_id → recipes(recipe_id) with CASCADE delete
    op.create_foreign_key(
        'portion_presets_recipe_id_fkey',
        'portion_presets',
        'recipes',
        ['recipe_id'],
        ['recipe_id'],
        ondelete='CASCADE'
    )
    
    # ==========================================
    # STEP 6: ADD INDEXES
    # ==========================================
    
    # Index on recipe_id for fast lookups
    op.create_index(
        'ix_portion_presets_recipe_id',
        'portion_presets',
        ['recipe_id']
    )
    
    # Partial index for default recipe presets (performance optimization)
    op.create_index(
        'ix_portion_presets_recipe_default',
        'portion_presets',
        ['recipe_id', 'is_default'],
        postgresql_where=sa.text('recipe_id IS NOT NULL AND is_default = true')
    )


def downgrade():
    """
    Revert to food-only portion_presets
    
    WARNING: This will delete all recipe portion presets!
    """
    
    # Drop indexes
    op.drop_index('ix_portion_presets_recipe_default', table_name='portion_presets')
    op.drop_index('ix_portion_presets_recipe_id', table_name='portion_presets')
    
    # Drop foreign key
    op.drop_constraint('portion_presets_recipe_id_fkey', 'portion_presets', type_='foreignkey')
    
    # Drop constraints
    op.drop_constraint('uq_portion_preset_item_size', 'portion_presets', type_='unique')
    op.drop_constraint('check_food_or_recipe_not_both', 'portion_presets', type_='check')
    
    # Remove recipe_id column (will delete all recipe presets!)
    op.drop_column('portion_presets', 'recipe_id')
    
    # Restore food_id as NOT NULL
    op.alter_column('portion_presets', 'food_id',
                    existing_type=UUID(),
                    nullable=False)
    
    # Recreate original unique constraint
    op.create_unique_constraint(
        'unique_food_size',
        'portion_presets',
        ['food_id', 'size_label']
    )
