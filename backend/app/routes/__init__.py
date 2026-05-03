"""
Routes Package
Exports all routers for easy import in main.py
"""

# Import all routers
from app.routes import auth
from app.routes import food
from app.routes import food_log
from app.routes import user
from app.routes import goal
from app.routes import admin
from app.routes import health_profile

# List available routers
__all__ = [
    "auth",
    "food",
    "food_log",
    "user",
    "goal",
    "admin",
    "health_profile"
]