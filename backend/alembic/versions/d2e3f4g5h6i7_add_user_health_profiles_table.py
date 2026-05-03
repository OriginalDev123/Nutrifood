"""add_user_health_profiles_table

Revision ID: d2e3f4g5h6i7
Revises: a3c8d9e2f4b1
Create Date: 2026-05-03 10:00:00.000000

Changes:
- Create user_health_profiles table for storing health conditions, allergies, dietary preferences
- Table stores user's health profile independently from user goals
- Each user can have only one health profile (unique user_id)

This table enables personalized meal planning based on:
- Health conditions (diabetes, hypertension, etc.)
- Food allergies (seafood, peanuts, gluten, etc.)
- Dietary preferences (low carb, keto, eat clean, etc.)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY


# revision identifiers, used by Alembic.
revision = 'd2e3f4g5h6i7'
down_revision = 'a3c8d9e2f4b1'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create user_health_profiles table
    """
    
    # Create the user_health_profiles table
    op.create_table(
        'user_health_profiles',
        sa.Column('profile_id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('health_conditions', ARRAY(sa.String()), nullable=True, server_default='{}'),
        sa.Column('food_allergies', ARRAY(sa.String()), nullable=True, server_default='{}'),
        sa.Column('dietary_preferences', ARRAY(sa.String()), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create index on user_id for faster lookups
    op.create_index('ix_user_health_profiles_user_id', 'user_health_profiles', ['user_id'], unique=True)
    
    # Add comment to table
    op.execute("COMMENT ON TABLE user_health_profiles IS 'Stores user health profile: conditions, allergies, dietary preferences'")


def downgrade():
    """
    Drop user_health_profiles table
    """
    op.drop_index('ix_user_health_profiles_user_id', 'user_health_profiles')
    op.drop_table('user_health_profiles')
