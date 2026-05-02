"""add_portion_presets_table

Revision ID: f1a2b3c4d5e6
Revises: b8e9242d1934
Create Date: 2026-03-02 10:00:00.000000

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'b8e9242d1934'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """
    Create portion_presets table for storing common portion sizes
    
    This table supports flexible unit systems:
    - Bowls (tô) for soups/noodles
    - Plates (dĩa) for rice dishes
    - Pieces (ổ, quả, miếng) for bread, eggs, fruits
    - Cans/Bottles (lon, chai) for drinks
    - Packs (gói) for snacks
    """
    
    # Ensure uuid-ossp extension is enabled (required for uuid_generate_v4())
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # ==========================================
    # CREATE PORTION_PRESETS TABLE
    # ==========================================
    op.create_table(
        'portion_presets',
        sa.Column('preset_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('food_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Size info
        sa.Column('size_label', sa.String(50), nullable=False, comment='Size identifier: small, medium, large, standard'),
        sa.Column('display_name_vi', sa.String(100), nullable=False, comment='Vietnamese display name: Tô nhỏ, Dĩa vừa, 1 ổ, etc'),
        sa.Column('display_name_en', sa.String(100), nullable=True, comment='English display name: Small bowl, Medium plate, 1 piece'),
        
        # Unit system
        sa.Column('unit_type', sa.String(30), nullable=False, comment='Unit type: bowl, plate, piece, can, bottle, glass, pack, slice'),
        sa.Column('unit_display_vi', sa.String(50), nullable=False, comment='Vietnamese unit: tô, dĩa, ổ, quả, lon, chai, gói, miếng'),
        sa.Column('unit_display_en', sa.String(50), nullable=True, comment='English unit: bowl, plate, piece, can, bottle, pack, slice'),
        
        # Portion data
        sa.Column('grams', sa.Integer, nullable=False, comment='Weight in grams'),
        
        # Metadata
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false', comment='Default selection for this food'),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0', comment='Display order (ascending)'),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Constraints
        sa.ForeignKeyConstraint(['food_id'], ['foods.food_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('food_id', 'size_label', name='unique_food_size'),
        sa.CheckConstraint('grams > 0', name='positive_grams'),
    )
    
    # ==========================================
    # CREATE INDEXES
    # ==========================================
    op.create_index('idx_portion_presets_food_id', 'portion_presets', ['food_id'])
    op.create_index(
        'idx_portion_presets_default', 
        'portion_presets', 
        ['food_id', 'is_default'], 
        postgresql_where=sa.text('is_default = true')
    )


def downgrade():
    """Drop portion_presets table and indexes"""
    
    op.drop_index('idx_portion_presets_default', table_name='portion_presets')
    op.drop_index('idx_portion_presets_food_id', table_name='portion_presets')
    op.drop_table('portion_presets')
