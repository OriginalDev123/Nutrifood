"""add_description_to_food_servings

Revision ID: add_desc_food_servings
Revises: 0ee452305acb
Create Date: 2026-04-07 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_desc_food_servings'
down_revision: Union[str, Sequence[str], None] = '0ee452305acb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Thêm column description cho bảng food_servings
    # Column này dùng để lưu mô tả định lượng như "1 bát (200g)", "100g", "1 quả"
    op.add_column('food_servings', sa.Column(
        'description',
        sa.String(255),
        nullable=True,
        comment='Serving description (e.g., "1 bát", "1 chén", "100g")'
    ))
    
    # Cập nhật giá trị mặc định cho description từ serving_unit
    # Vì serving_unit đã có giá trị, ta có thể copy qua
    op.execute("""
        UPDATE food_servings 
        SET description = serving_unit 
        WHERE description IS NULL
    """)


def downgrade() -> None:
    # Xóa column description
    op.drop_column('food_servings', 'description')
