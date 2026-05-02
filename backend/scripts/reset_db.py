"""
⚠️  DANGER ZONE ⚠️
Reset Database - DROP ALL TABLES!

Only use in development/testing!
NEVER run this in production!
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import engine, Base
from app.config import settings

def reset_database():
    """Drop all tables and recreate via Alembic"""
    
    if settings.ENVIRONMENT == "production":
        print("❌ Cannot reset database in PRODUCTION!")
        print("   Change ENVIRONMENT in .env to 'development' first")
        return
    
    print("\n" + "="*60)
    print("⚠️  WARNING: This will DELETE ALL DATA! ⚠️")
    print("="*60)
    confirm = input("Type 'DELETE ALL DATA' to confirm: ")
    
    if confirm != "DELETE ALL DATA":
        print("❌ Cancelled")
        return
    
    print("\n🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped!")
    
    print("\n📝 Now run Alembic migrations:")
    print("   alembic upgrade head")

if __name__ == "__main__":
    reset_database()