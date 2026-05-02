"""change_instructions_steps_to_jsonb

Revision ID: b8e9242d1934
Revises: 954b5611f119
Create Date: 2026-01-15 01:59:00.183213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b8e9242d1934'
down_revision: Union[str, None] = '954b5611f119'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Sử dụng lệnh SQL thuần để ép kiểu phức tạp thông qua bước trung gian là ARRAY_TO_JSON
    op.execute(
        'ALTER TABLE recipes ALTER COLUMN instructions_steps TYPE JSONB '
        'USING to_jsonb(array_to_json(instructions_steps))'
    )
    
    # Cập nhật lại các thuộc tính khác như comment và nullable để đồng bộ với Model
    op.alter_column('recipes', 'instructions_steps',
               existing_type=postgresql.JSONB(),
               comment='Structured cooking steps (JSON format)',
               existing_nullable=True)


def downgrade() -> None:
    # Ép kiểu ngược lại từ JSONB sang TEXT ARRAY nếu cần quay lại phiên bản cũ
    op.execute(
        'ALTER TABLE recipes ALTER COLUMN instructions_steps TYPE TEXT[] '
        'USING ARRAY(SELECT jsonb_array_elements_text(instructions_steps))'
    )
    
    op.alter_column('recipes', 'instructions_steps',
               existing_type=postgresql.ARRAY(sa.TEXT()),
               comment='Structured cooking steps',
               existing_nullable=True)