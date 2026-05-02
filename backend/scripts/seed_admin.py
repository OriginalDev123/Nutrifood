"""
Seed Admin Account Script
Creates a default admin account for NutriAI

Usage:
    python -m scripts.seed_admin

Default admin credentials:
    Email: admin@nutriai.vn
    Password: Admin123
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models.user import User
from app.utils.security import get_password_hash


def seed_admin():
    """Create or verify admin account exists"""
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(
            User.email == "admin@nutriai.vn"
        ).first()
        
        if existing_admin:
            print(f"✅ Admin account already exists: {existing_admin.email}")
            print(f"   - User ID: {existing_admin.user_id}")
            print(f"   - Is Admin: {existing_admin.is_admin}")
            print(f"   - Is Active: {existing_admin.is_active}")
            return existing_admin
        
        # Create new admin account
        admin = User(
            email="admin@nutriai.vn",
            password_hash=get_password_hash("Admin123"),
            full_name="NutriAI Administrator",
            is_active=True,
            is_admin=True,
            email_verified=True,
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("=" * 60)
        print("🎉 ADMIN ACCOUNT CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"   Email:    admin@nutriai.vn")
        print(f"   Password: Admin123")
        print(f"   User ID:  {admin.user_id}")
        print("=" * 60)
        print()
        print("⚠️  Please change the password after first login!")
        print()
        
        return admin
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin account: {e}")
        raise
    finally:
        db.close()


def seed_super_admin(email: str, password: str, full_name: str = "Super Admin"):
    """Create a custom super admin account"""
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == email).first()
        
        if existing:
            print(f"⚠️  User with email {email} already exists")
            existing.is_admin = True
            db.commit()
            print(f"✅ Updated existing user to admin")
            return existing
        
        # Create new admin
        admin = User(
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            is_active=True,
            is_admin=True,
            email_verified=True,
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print(f"✅ Admin created: {email}")
        return admin
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print()
    print("🍎 NutriAI - Admin Account Seeder")
    print("=" * 60)
    
    # Create default admin
    seed_admin()
    
    print()
    print("=" * 60)
    print("📝 To create additional admin accounts, use:")
    print("   seed_super_admin('admin@example.com', 'Password123', 'Admin Name')")
    print("=" * 60)
