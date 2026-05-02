"""update_foods_table_structure

Revision ID: 954b5611f119
Revises: de78b295d9d0
Create Date: 2026-01-13 14:40:11.453439

Changes from seed script schema to proper schema:
- Rename 'calories' -> 'calories_per_100g'
- Rename 'protein_g' -> 'protein_per_100g'
- Rename 'carbs_g' -> 'carbs_per_100g'
- Rename 'fat_g' -> 'fat_per_100g'
- Rename 'fiber_g' -> 'fiber_per_100g'
- Rename 'sugar_g' -> 'sugar_per_100g'
- Rename 'sodium_mg' -> 'sodium_per_100g'
- Rename 'cholesterol_mg' -> 'cholesterol_mg_per_100g' (add column)
- Rename 'saturated_fat_g' -> 'saturated_fat_g_per_100g' (add column)
- Rename 'serving_size_g' -> 'serving_size_g' (keep)
- Add: name_en, cuisine_type, created_by columns
- Add: is_deleted, deleted_at soft delete columns
- Rename serving_unit -> unit (keep)
- Drop: unit column (foods table doesn't need it; it's in food_servings)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '954b5611f119'
down_revision: Union[str, Sequence[str], None] = 'de78b295d9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================
    # 1. RENAME NUTRITION COLUMNS (seed script → proper schema)
    # ==========================================
    # Rename columns from seed script names to proper per_100g names
    renames = [
        ('calories', 'calories_per_100g'),
        ('protein_g', 'protein_per_100g'),
        ('carbs_g', 'carbs_per_100g'),
        ('fat_g', 'fat_per_100g'),
        ('fiber_g', 'fiber_per_100g'),
        ('sugar_g', 'sugar_per_100g'),
        ('sodium_mg', 'sodium_per_100g'),
    ]
    for old_name, new_name in renames:
        op.execute(
            f'ALTER TABLE foods RENAME COLUMN "{old_name}" TO "{new_name}"'
        )

    # ==========================================
    # 2. ADD NEW COLUMNS
    # ==========================================
    op.add_column('foods', sa.Column('name_en', sa.String(255), nullable=True,
                  comment='Food name in English'))
    op.add_column('foods', sa.Column('cuisine_type', sa.String(50), nullable=True,
                  comment='Cuisine type'))
    op.add_column('foods', sa.Column('created_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.user_id', ondelete='SET NULL'),
                  nullable=True,
                  comment='User who created this food'))

    # ==========================================
    # 3. ADD SOFT DELETE COLUMNS
    # ==========================================
    op.add_column('foods', sa.Column('is_deleted', sa.Boolean,
                  server_default=sa.text('false'),
                  nullable=False,
                  comment='Trạng thái xóa (False=Active, True=Deleted)'))
    op.add_column('foods', sa.Column('deleted_at', sa.DateTime(timezone=True),
                  nullable=True,
                  comment='Soft delete timestamp'))

    # ==========================================
    # 4. FOOD_SERVINGS SOFT DELETE COLUMNS
    # ==========================================
    op.add_column('food_servings', sa.Column('is_deleted', sa.Boolean,
                  server_default=sa.text('false'),
                  nullable=False,
                  comment='Trạng thái xóa (False=Active, True=Deleted)'))
    op.add_column('food_servings', sa.Column('deleted_at', sa.DateTime(timezone=True),
                  nullable=True,
                  comment='Soft delete timestamp'))

    # ==========================================
    # 5. ADD INDEXES
    # ==========================================
    op.create_index('ix_foods_is_deleted', 'foods', ['is_deleted'])
    op.create_index('ix_food_servings_is_deleted', 'food_servings', ['is_deleted'])

    # ==========================================
    # 6. ADD CHECK CONSTRAINTS
    # ==========================================
    op.create_check_constraint(
        'valid_calories', 'foods',
        'calories_per_100g >= 0'
    )
    op.create_check_constraint(
        'valid_protein', 'foods',
        'protein_per_100g >= 0'
    )
    op.create_check_constraint(
        'valid_carbs', 'foods',
        'carbs_per_100g >= 0'
    )
    op.create_check_constraint(
        'valid_fat', 'foods',
        'fat_per_100g >= 0'
    )
    op.create_check_constraint(
        'valid_source', 'foods',
        "source IN ('admin', 'usda', 'user_submitted')"
    )


def downgrade() -> None:
    # Drop constraints
    op.drop_constraint('valid_source', 'foods', type_='check')
    op.drop_constraint('valid_fat', 'foods', type_='check')
    op.drop_constraint('valid_carbs', 'foods', type_='check')
    op.drop_constraint('valid_protein', 'foods', type_='check')
    op.drop_constraint('valid_calories', 'foods', type_='check')

    # Drop indexes
    op.drop_index('ix_food_servings_is_deleted', table_name='food_servings')
    op.drop_index('ix_foods_is_deleted', table_name='foods')

    # Drop soft delete columns
    op.drop_column('food_servings', 'deleted_at')
    op.drop_column('food_servings', 'is_deleted')
    op.drop_column('foods', 'deleted_at')
    op.drop_column('foods', 'is_deleted')

    # Drop new columns
    op.drop_column('foods', 'created_by')
    op.drop_column('foods', 'cuisine_type')
    op.drop_column('foods', 'name_en')

    # Rename columns back to seed script names
    renames = [
        ('sodium_per_100g', 'sodium_mg'),
        ('sugar_per_100g', 'sugar_g'),
        ('fiber_per_100g', 'fiber_g'),
        ('fat_per_100g', 'fat_g'),
        ('carbs_per_100g', 'carbs_g'),
        ('protein_per_100g', 'protein_g'),
        ('calories_per_100g', 'calories'),
    ]
    for old_name, new_name in renames:
        op.execute(
            f'ALTER TABLE foods RENAME COLUMN "{old_name}" TO "{new_name}"'
        )
