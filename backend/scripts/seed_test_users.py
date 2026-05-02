"""
NutriAI - Test Users Seed Generator v1.0
Logic: Tạo test users với profiles và goals để test Module 3, 4, 5, 6
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta

# Setup import path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.user import User, UserProfile, UserGoal
from app.utils.security import get_password_hash

db = SessionLocal()

# ==========================================
# TEST USERS DATA
# ==========================================

TEST_USERS = [
    {
        "email": "test1@nutriai.com",
        "password": "Test123!",  # Simple test password
        "full_name": "Nguyễn Văn A",
        "is_active": True,
        "email_verified": True,
        "profile": {
            "date_of_birth": date(1995, 3, 15),
            "gender": "male",
            "height_cm": Decimal("175.00"),
            "activity_level": "moderately_active",
            "timezone": "Asia/Ho_Chi_Minh",
            "language": "vi"
        },
        "goal": {
            "goal_type": "weight_loss",
            "current_weight_kg": Decimal("80.00"),
            "target_weight_kg": Decimal("75.00"),
            "target_date": date.today() + timedelta(days=90),  # 3 months
            "daily_calorie_target": 2000,
            "protein_target_g": 150,
            "carbs_target_g": 200,
            "fat_target_g": 60,
            "health_conditions": [],
            "food_allergies": ["peanuts"],
            "dietary_preferences": ["low_carb"],
            "is_active": True
        }
    },
    {
        "email": "test2@nutriai.com",
        "password": "Test123!",
        "full_name": "Trần Thị B",
        "is_active": True,
        "email_verified": True,
        "profile": {
            "date_of_birth": date(1998, 7, 22),
            "gender": "female",
            "height_cm": Decimal("160.00"),
            "activity_level": "lightly_active",
            "timezone": "Asia/Ho_Chi_Minh",
            "language": "vi"
        },
        "goal": {
            "goal_type": "maintain",
            "current_weight_kg": Decimal("55.00"),
            "target_weight_kg": Decimal("55.00"),
            "target_date": None,
            "daily_calorie_target": 1800,
            "protein_target_g": 120,
            "carbs_target_g": 180,
            "fat_target_g": 60,
            "health_conditions": [],
            "food_allergies": [],
            "dietary_preferences": ["vegetarian"],
            "is_active": True
        }
    },
    {
        "email": "test3@nutriai.com",
        "password": "Test123!",
        "full_name": "Lê Minh C",
        "is_active": True,
        "email_verified": True,
        "profile": {
            "date_of_birth": date(1992, 11, 8),
            "gender": "male",
            "height_cm": Decimal("168.00"),
            "activity_level": "very_active",
            "timezone": "Asia/Ho_Chi_Minh",
            "language": "vi"
        },
        "goal": {
            "goal_type": "weight_gain",
            "current_weight_kg": Decimal("65.00"),
            "target_weight_kg": Decimal("70.00"),
            "target_date": date.today() + timedelta(days=120),  # 4 months
            "daily_calorie_target": 2800,
            "protein_target_g": 180,
            "carbs_target_g": 350,
            "fat_target_g": 80,
            "health_conditions": [],
            "food_allergies": ["shellfish", "dairy"],
            "dietary_preferences": [],
            "is_active": True
        }
    },
    {
        "email": "test4@nutriai.com",
        "password": "Test123!",
        "full_name": "Phạm Thu D",
        "is_active": True,
        "email_verified": True,
        "profile": {
            "date_of_birth": date(2000, 5, 30),
            "gender": "female",
            "height_cm": Decimal("165.00"),
            "activity_level": "sedentary",
            "timezone": "Asia/Ho_Chi_Minh",
            "language": "vi"
        },
        "goal": {
            "goal_type": "healthy_lifestyle",
            "current_weight_kg": Decimal("58.00"),
            "target_weight_kg": Decimal("58.00"),
            "target_date": None,
            "daily_calorie_target": 1600,
            "protein_target_g": 100,
            "carbs_target_g": 160,
            "fat_target_g": 55,
            "health_conditions": ["diabetes"],
            "food_allergies": [],
            "dietary_preferences": ["low_sugar"],
            "is_active": True
        }
    }
]

# ==========================================
# SEED FUNCTION
# ==========================================

def seed_test_users():
    """Seed test users with profiles and goals"""
    
    print("=" * 60)
    print("SEED TEST USERS")
    print("=" * 60)
    
    created_users = []
    
    for user_data in TEST_USERS:
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(
                User.email == user_data["email"]
            ).first()
            
            if existing_user:
                print(f"⏭️  User {user_data['email']} already exists, skipping...")
                continue
            
            # 1. Create User
            new_user = User(
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                is_active=user_data["is_active"],
                email_verified=user_data["email_verified"]
            )
            db.add(new_user)
            db.flush()  # Get user_id without committing
            
            # 2. Create UserProfile
            profile_data = user_data["profile"]
            new_profile = UserProfile(
                user_id=new_user.user_id,
                **profile_data
            )
            db.add(new_profile)
            
            # 3. Create UserGoal
            goal_data = user_data["goal"]
            new_goal = UserGoal(
                user_id=new_user.user_id,
                **goal_data
            )
            db.add(new_goal)
            
            db.commit()
            
            created_users.append(new_user)
            print(f"✅ Created user: {new_user.full_name} ({new_user.email})")
            print(f"   Goal: {goal_data['goal_type']}, Target: {goal_data.get('target_weight_kg', 'N/A')} kg")
            print(f"   Daily calories: {goal_data['daily_calorie_target']} kcal")
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error creating user {user_data['email']}: {str(e)}")
            continue
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: Created {len(created_users)} test users")
    print("=" * 60)
    
    # Return first user for food logging
    return created_users[0] if created_users else None


if __name__ == "__main__":
    try:
        first_user = seed_test_users()
        if first_user:
            print(f"\n💡 First test user ID for food logs: {first_user.user_id}")
    finally:
        db.close()
