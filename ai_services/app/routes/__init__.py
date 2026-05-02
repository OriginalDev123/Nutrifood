"""API routes package for ai_services."""
"""
NutriAI AI Service
Main package initialization
"""

__version__ = "1.0.0"
__author__ = "NutriAI Team"

# File này giúp Python nhận diện app/ là một package

# === app/routes/__init__.py ===
# Import routers để dễ sử dụng
from app.routes import vision, nutrition, chat, analytics, meal_planning, advice
