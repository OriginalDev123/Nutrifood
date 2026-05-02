"""
Seed Recipe Portion Presets

This script populates the portion_presets table with common portion sizes for RECIPES.

Priority: RECIPES > FOODS for Vision AI
- Vision AI will primarily detect prepared dishes (recipes)
- Portion presets help users select accurate serving sizes

Usage:
    # Dry run (preview changes)
    python -m scripts.seed_recipe_portion_presets --dry-run
    
    # Execute seeding
    python -m scripts.seed_recipe_portion_presets
"""

import logging
import sys
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.recipe import Recipe
from app.models.food import PortionPreset

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


# ==========================================
# UNIT CONFIGURATIONS FOR RECIPES
# ==========================================
# Recipes typically use plate/bowl serving sizes

RECIPE_UNIT_CONFIGS = {
    # For rice dishes, stir-fries, grilled meats
    "plate": {
        "unit_type": "plate",
        "unit_display_vi": "dĩa",
        "unit_display_en": "plate",
        "sizes": [
            {
                "label": "small",
                "display_vi": "Phần nhỏ",
                "display_en": "Small portion",
                "grams": 250,
                "is_default": False,
                "sort_order": 1
            },
            {
                "label": "medium",
                "display_vi": "Phần vừa",
                "display_en": "Medium portion",
                "grams": 350,
                "is_default": True,
                "sort_order": 2
            },
            {
                "label": "large",
                "display_vi": "Phần lớn",
                "display_en": "Large portion",
                "grams": 500,
                "is_default": False,
                "sort_order": 3
            }
        ]
    },
    
    # For soups, noodle soups, pho
    "bowl": {
        "unit_type": "bowl",
        "unit_display_vi": "tô",
        "unit_display_en": "bowl",
        "sizes": [
            {
                "label": "small",
                "display_vi": "Tô nhỏ",
                "display_en": "Small bowl",
                "grams": 300,
                "is_default": False,
                "sort_order": 1
            },
            {
                "label": "medium",
                "display_vi": "Tô vừa",
                "display_en": "Medium bowl",
                "grams": 450,
                "is_default": True,
                "sort_order": 2
            },
            {
                "label": "large",
                "display_vi": "Tô lớn",
                "display_en": "Large bowl",
                "grams": 600,
                "is_default": False,
                "sort_order": 3
            }
        ]
    }
}


# ==========================================
# RECIPE CATEGORY → UNIT TYPE MAPPING
# ==========================================
# Maps recipe categories to appropriate unit types

CATEGORY_UNIT_MAPPING = {
    # Main dishes, grilled items, stir-fries → plate
    "Healthy": "plate",
    "Balanced": "plate",
    "Keto": "plate",
    "High-Protein": "plate",
    
    # Soups → bowl
    "Soup": "bowl",
    
    # Default fallback
    "default": "plate"
}


# ==========================================
# SPECIFIC RECIPE NAME PATTERNS → UNIT TYPE
# ==========================================
# Override category mapping based on recipe name

RECIPE_NAME_PATTERNS = {
    # Soups (canh, súp, phở, bún)
    "bowl": [
        "canh", "súp", "phở", "bún", "hủ tiếu", "mì", "miến",
        "cháo", "soup"
    ],
    
    # Everything else defaults to plate
}


def get_unit_type_for_recipe(recipe: Recipe) -> str:
    """
    Determine the appropriate unit type for a recipe
    
    Priority:
    1. Recipe name pattern (canh, phở, bún → bowl)
    2. Recipe category (Soup → bowl)
    3. Default → plate
    """
    name_lower = recipe.name_vi.lower()
    
    # Check name patterns first
    for unit_type, patterns in RECIPE_NAME_PATTERNS.items():
        for pattern in patterns:
            if pattern in name_lower:
                return unit_type
    
    # Check category mapping
    category = recipe.category or "default"
    return CATEGORY_UNIT_MAPPING.get(category, "plate")


def generate_presets_for_recipe(recipe: Recipe, db: Session) -> list[PortionPreset]:
    """
    Generate portion presets for a single recipe
    
    Returns list of PortionPreset objects (not yet committed)
    """
    # Determine unit type
    unit_type = get_unit_type_for_recipe(recipe)
    unit_config = RECIPE_UNIT_CONFIGS.get(unit_type, RECIPE_UNIT_CONFIGS["plate"])
    
    presets = []
    for size in unit_config["sizes"]:
        preset = PortionPreset(
            recipe_id=recipe.recipe_id,
            food_id=None,  # This is a recipe preset
            size_label=size["label"],
            display_name_vi=size["display_vi"],
            display_name_en=size["display_en"],
            unit_type=unit_config["unit_type"],
            unit_display_vi=unit_config["unit_display_vi"],
            unit_display_en=unit_config["unit_display_en"],
            grams=size["grams"],
            is_default=size["is_default"],
            sort_order=size["sort_order"]
        )
        presets.append(preset)
    
    return presets


def seed_recipe_portion_presets(dry_run: bool = False):
    """
    Main seeding function
    
    Args:
        dry_run: If True, preview changes without committing
    """
    logger.info("🚀 Starting recipe portion presets seeding...")
    logger.info(f"   Dry run: {dry_run}")
    
    db = next(get_db())
    
    try:
        # Get all active recipes (prioritize verified ones)
        recipes_query = select(Recipe).where(
            Recipe.is_deleted == False,
            Recipe.is_verified == True  # Only verified recipes
        ).order_by(Recipe.name_vi)
        
        recipes = db.execute(recipes_query).scalars().all()
        
        if not recipes:
            logger.warning("⚠️  No verified recipes found in database")
            return
        
        logger.info(f"📊 Found {len(recipes)} verified recipes")
        
        total_created = 0
        recipes_processed = 0
        
        for recipe in recipes:
            # Check if presets already exist
            existing_presets = db.execute(
                select(PortionPreset).where(
                    PortionPreset.recipe_id == recipe.recipe_id
                )
            ).scalars().all()
            
            if existing_presets:
                logger.info(f"⏭️  Skipping: {recipe.name_vi} (already has {len(existing_presets)} presets)")
                continue
            
            # Generate presets
            presets = generate_presets_for_recipe(recipe, db)
            
            # Add to session
            for preset in presets:
                db.add(preset)
            
            unit_type = get_unit_type_for_recipe(recipe)
            logger.info(f"📦 Processing: {recipe.name_vi}")
            logger.info(f"   Unit type: {unit_type}")
            logger.info(f"   ✅ Created {len(presets)} presets")
            
            total_created += len(presets)
            recipes_processed += 1
        
        if dry_run:
            logger.info(f"\n🔄 Dry run mode - rolling back changes")
            db.rollback()
        else:
            logger.info(f"\n💾 Committing changes to database...")
            db.commit()
        
        logger.info(f"\n{'=' * 50}")
        logger.info(f"✅ Seeding complete!")
        logger.info(f"   Recipes processed: {recipes_processed}")
        logger.info(f"   Presets created: {total_created}")
        logger.info(f"{'=' * 50}")
        
    except Exception as e:
        logger.error(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Parse command line arguments
    dry_run = "--dry-run" in sys.argv
    
    seed_recipe_portion_presets(dry_run=dry_run)
