"""
Alembic Environment Configuration

This file connects Alembic to:
1. Our database (via DATABASE_URL)
2. Our SQLAlchemy models (via Base.metadata)
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlalchemy import create_engine
from app.models.food import Food, FoodServing
from app.models.food_log import FoodLog, WeightLog

# ============================================
# IMPORTANT: Import our config and models
# ============================================
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import our database config and models
from app.config import settings
from app.database import Base

# Import ALL models here so Alembic can detect them
from app.models.user import User, UserProfile, UserGoal

# ⬇️ Khi tạo models mới, PHẢI import ở đây!
# from app.models.food import Food, FoodServing
# from app.models.food_log import FoodLog, WeightLog
# ... etc

# ============================================
# Alembic Config
# ============================================

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url from alembic.ini with our DATABASE_URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# ============================================
# Offline Mode (generate SQL script)
# ============================================

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This generates SQL script without connecting to database.
    Useful for generating .sql files for review.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================
# Online Mode (direct database connection)
# ============================================

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    This connects to database and executes migrations directly.
    This is the normal mode used in development and production.
    """
    
    # Create engine with our settings
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Don't use connection pool for migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect column type changes
            compare_server_default=True,  # Detect default changes
            include_schemas=False,  # Don't include other schemas
            render_as_batch=False,  # Not needed for PostgreSQL
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================
# Main Entry Point
# ============================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()