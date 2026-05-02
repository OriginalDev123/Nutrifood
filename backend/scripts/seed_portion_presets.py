"""
Seed Portion Presets

This script populates the portion_presets table with common serving sizes
for popular Vietnamese foods using a flexible unit system.

Unit Types:
- bowl (tô): Soups and noodles
- plate (dĩa): Rice dishes  
- piece (ổ, quả, miếng): Bread, eggs, fruits
- can (lon), bottle (chai): Drinks
- pack (gói): Snacks

Usage:
    python -m backend.scripts.seed_portion_presets
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Food, PortionPreset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==========================================
# UNIT CONFIGURATIONS
# ==========================================

UNIT_CONFIGS = {
    # Soup/Noodles - Bowls
    'bowl': {
        'unit_type': 'bowl',
        'unit_display_vi': 'tô',
        'unit_display_en': 'bowl',
        'sizes': [
            {'label': 'small', 'display_vi': 'Tô nhỏ', 'display_en': 'Small bowl', 'grams': 350},
            {'label': 'medium', 'display_vi': 'Tô vừa', 'display_en': 'Medium bowl', 'grams': 500, 'default': True},
            {'label': 'large', 'display_vi': 'Tô lớn', 'display_en': 'Large bowl', 'grams': 650},
        ]
    },
    
    # Rice dishes - Plates
    'plate': {
        'unit_type': 'plate',
        'unit_display_vi': 'dĩa',
        'unit_display_en': 'plate',
        'sizes': [
            {'label': 'small', 'display_vi': 'Dĩa nhỏ', 'display_en': 'Small plate', 'grams': 300},
            {'label': 'medium', 'display_vi': 'Dĩa vừa', 'display_en': 'Medium plate', 'grams': 400, 'default': True},
            {'label': 'large', 'display_vi': 'Dĩa lớn', 'display_en': 'Large plate', 'grams': 550},
        ]
    },
    
    # Bread - Pieces
    'bread': {
        'unit_type': 'piece',
        'unit_display_vi': 'ổ',
        'unit_display_en': 'piece',
        'sizes': [
            {'label': 'small', 'display_vi': '1 ổ nhỏ', 'display_en': '1 small piece', 'grams': 150},
            {'label': 'medium', 'display_vi': '1 ổ vừa', 'display_en': '1 medium piece', 'grams': 180, 'default': True},
            {'label': 'large', 'display_vi': '1 ổ lớn', 'display_en': '1 large piece', 'grams': 220},
        ]
    },
    
    # Drinks - Cans
    'can': {
        'unit_type': 'can',
        'unit_display_vi': 'lon',
        'unit_display_en': 'can',
        'sizes': [
            {'label': 'standard', 'display_vi': '1 lon (330ml)', 'display_en': '1 can (330ml)', 'grams': 330, 'default': True},
        ]
    },
    
    # Drinks - Bottles
    'bottle': {
        'unit_type': 'bottle',
        'unit_display_vi': 'chai',
        'unit_display_en': 'bottle',
        'sizes': [
            {'label': 'small', 'display_vi': '1 chai nhỏ (500ml)', 'display_en': '1 small bottle (500ml)', 'grams': 500, 'default': True},
            {'label': 'large', 'display_vi': '1 chai lớn (1.5L)', 'display_en': '1 large bottle (1.5L)', 'grams': 1500},
        ]
    },
    
    # Drinks - Glass
    'glass': {
        'unit_type': 'glass',
        'unit_display_vi': 'ly',
        'unit_display_en': 'glass',
        'sizes': [
            {'label': 'small', 'display_vi': '1 ly nhỏ (200ml)', 'display_en': '1 small glass (200ml)', 'grams': 200},
            {'label': 'medium', 'display_vi': '1 ly vừa (250ml)', 'display_en': '1 medium glass (250ml)', 'grams': 250, 'default': True},
            {'label': 'large', 'display_vi': '1 ly lớn (350ml)', 'display_en': '1 large glass (350ml)', 'grams': 350},
        ]
    },
    
    # Eggs/Fruits - Countable pieces
    'countable': {
        'unit_type': 'piece',
        'unit_display_vi': 'quả',
        'unit_display_en': 'piece',
        'sizes': [
            {'label': 'single', 'display_vi': '1 quả', 'display_en': '1 piece', 'grams': 50, 'default': True},
            {'label': 'double', 'display_vi': '2 quả', 'display_en': '2 pieces', 'grams': 100},
            {'label': 'triple', 'display_vi': '3 quả', 'display_en': '3 pieces', 'grams': 150},
        ]
    },
    
    # Snacks - Packs
    'snack': {
        'unit_type': 'pack',
        'unit_display_vi': 'gói',
        'unit_display_en': 'pack',
        'sizes': [
            {'label': 'small', 'display_vi': '1 gói nhỏ', 'display_en': '1 small pack', 'grams': 50, 'default': True},
            {'label': 'large', 'display_vi': '1 gói lớn', 'display_en': '1 large pack', 'grams': 150},
        ]
    },
}


# ==========================================
# FOOD-TO-UNIT MAPPING
# ==========================================

FOOD_UNIT_MAPPING = {
    # Noodle soups - Bowl
    'Phở bò': 'bowl',
    'Phở gà': 'bowl',
    'Bún bò Huế': 'bowl',
    'Bún chả': 'bowl',
    'Bún riêu': 'bowl',
    'Hủ tiếu': 'bowl',
    'Mì Quảng': 'bowl',
    'Bánh canh': 'bowl',
    
    # Rice dishes - Plate
    'Cơm tấm': 'plate',
    'Cơm tấm sườn': 'plate',
    'Cơm chiên': 'plate',
    'Cơm gà': 'plate',
    'Xôi': 'plate',
    
    # Bread - Piece
    'Bánh mì': 'bread',
    'Bánh mì thịt': 'bread',
    'Bánh mì pate': 'bread',
    'Bánh bao': 'countable',
    
    # Drinks - Can/Bottle
    'Coca Cola': 'can',
    'Pepsi': 'can',
    'Nước ngọt': 'can',
    'Trà': 'glass',
    'Cà phê': 'glass',
    'Nước cam': 'glass',
    
    # Eggs - Countable
    'Trứng gà': 'countable',
    'Trứng vịt': 'countable',
    
    # Snacks - Pack
    'Snack': 'snack',
}


def generate_presets_for_food(db: Session, food: Food, unit_config_key: str) -> int:
    """
    Generate portion presets for a food based on unit configuration
    
    Args:
        db: Database session
        food: Food model instance
        unit_config_key: Key in UNIT_CONFIGS (e.g., 'bowl', 'plate')
    
    Returns:
        Number of presets created
    """
    
    if unit_config_key not in UNIT_CONFIGS:
        logger.warning(f"Unknown unit config: {unit_config_key}")
        return 0
    
    unit_config = UNIT_CONFIGS[unit_config_key]
    count = 0
    
    for i, size in enumerate(unit_config['sizes']):
        # Check if preset already exists
        existing = db.query(PortionPreset).filter(
            PortionPreset.food_id == food.food_id,
            PortionPreset.size_label == size['label']
        ).first()
        
        if existing:
            logger.debug(f"   Preset already exists: {food.name_vi} - {size['display_vi']}")
            continue
        
        # Create new preset
        preset = PortionPreset(
            food_id=food.food_id,
            size_label=size['label'],
            display_name_vi=size['display_vi'],
            display_name_en=size.get('display_en', size['display_vi']),
            unit_type=unit_config['unit_type'],
            unit_display_vi=unit_config['unit_display_vi'],
            unit_display_en=unit_config['unit_display_en'],
            grams=size['grams'],
            is_default=size.get('default', False),
            sort_order=i + 1
        )
        
        db.add(preset)
        count += 1
        logger.debug(f"   ✓ Created: {size['display_vi']} ({size['grams']}g)")
    
    return count


def seed_portion_presets(db: Session, dry_run: bool = False):
    """
    Seed portion presets for popular Vietnamese foods
    
    Args:
        db: Database session
        dry_run: If True, don't commit changes
    """
    
    logger.info("🚀 Starting portion presets seeding...")
    logger.info(f"   Dry run: {dry_run}")
    
    total_foods = 0
    total_presets = 0
    
    # Process foods with known unit mappings
    for food_name, unit_config_key in FOOD_UNIT_MAPPING.items():
        # Find food (case-insensitive, partial match)
        food = db.query(Food).filter(
            Food.name_vi.ilike(f'%{food_name}%'),
            Food.is_deleted == False
        ).first()
        
        if not food:
            logger.warning(f"⚠️  Food not found: {food_name}")
            continue
        
        logger.info(f"📦 Processing: {food.name_vi}")
        
        presets_created = generate_presets_for_food(db, food, unit_config_key)
        
        if presets_created > 0:
            total_foods += 1
            total_presets += presets_created
            logger.info(f"   ✅ Created {presets_created} presets")
        else:
            logger.info(f"   ℹ️  No new presets (already exist)")
    
    # Commit or rollback
    if dry_run:
        logger.info("\n🔄 Dry run mode - rolling back changes")
        db.rollback()
    else:
        logger.info("\n💾 Committing changes to database...")
        db.commit()
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("✅ Seeding complete!")
    logger.info(f"   Foods processed: {total_foods}")
    logger.info(f"   Presets created: {total_presets}")
    logger.info("="*50)


def main():
    """Main execution"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed portion presets')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without committing')
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        seed_portion_presets(db, dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
