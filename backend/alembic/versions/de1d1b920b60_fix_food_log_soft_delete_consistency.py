"""fix_food_log_soft_delete_consistency

Revision ID: de1d1b920b60
Revises: 0ee452305acb
Create Date: 2026-01-07 16:35:33.435386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'de1d1b920b60'
down_revision: Union[str, None] = '0ee452305acb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # food_logs soft delete columns are already created in v001 migration
    # This migration is kept for historical consistency
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # No-op: v001 already handles food_logs structure
    pass
    # ### end Alembic commands ###
