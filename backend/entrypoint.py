"""
NutriAI - Entrypoint Script (Pure Python)
Seed dữ liệu thực phẩm khi container khởi động
"""

import sys
import time
from pathlib import Path

# Add /app to path
sys.path.insert(0, '/app')

from app.database import SessionLocal, engine, Base
import app.models
from app.models.food import Food, FoodServing


def wait_for_db(max_attempts=30):
    """Đợi PostgreSQL sẵn sàng"""
    for i in range(max_attempts):
        try:
            conn = engine.connect()
            conn.close()
            return True
        except Exception:
            if i < max_attempts - 1:
                time.sleep(2)
    return False


def create_tables():
    """Tạo tất cả các bảng trong database"""
    print("   🗄️  Đang tạo database tables...")
    Base.metadata.create_all(bind=engine)
    print("   ✅ Database tables đã được tạo!")


def seed_foods():
    """Seed dữ liệu thực phẩm"""
    from scripts.seed_foods import FOODS_DATA

    db = SessionLocal()
    count_success = 0
    count_skip = 0

    print("   🚀 Bắt đầu seed dữ liệu thực phẩm...")

    for data in FOODS_DATA:
        # Check if food already exists
        existing = db.query(Food).filter(
            Food.name_vi == data['name_vi']
        ).first()

        if existing:
            count_skip += 1
            continue

        try:
            # Create food without servings first
            food_data = {k: v for k, v in data.items() if k != 'servings'}
            food = Food(**food_data)
            db.add(food)
            db.flush()

            # Create servings
            for idx, s in enumerate(data.get('servings', [])):
                serving = FoodServing(
                    food_id=food.food_id,
                    serving_unit=s['description'],  # Trường bắt buộc trong DB
                    description=s['description'],  # Trường tùy chọn (nullable)
                    serving_size_g=s['size_g'],
                    is_default=s.get('is_default', idx == 0)
                )
                db.add(serving)

            db.commit()
            count_success += 1
            print(f"   ✅ {data['name_vi']}")

        except Exception as e:
            db.rollback()
            print(f"   ❌ Lỗi: {data['name_vi']} - {str(e)[:50]}")

    print(f"   📊 Tổng kết: {count_success} thành công, {count_skip} bỏ qua")
    db.close()
    return count_success


def main():
    print("=" * 60)
    print("🍎 NutriAI Backend Starting...")
    print("=" * 60)

    # Chờ database
    print("📦 Đang chờ PostgreSQL...")
    if not wait_for_db():
        print("   ❌ PostgreSQL không sẵn sàng!")
        sys.exit(1)
    else:
        print("   ✅ PostgreSQL đã sẵn sàng!")

    # Tạo tables trước khi query
    print("")
    print("🗄️  Đang khởi tạo database...")
    create_tables()

    # Kiểm tra và seed dữ liệu
    print("")
    print("📊 Đang kiểm tra dữ liệu...")

    db = SessionLocal()
    count = db.query(Food).count()
    print(f"   📊 Số thực phẩm trong DB: {count}")
    db.close()

    if count == 0:
        print("   ⚠️  Database trống! Đang seed dữ liệu...")
        seed_foods()
    elif count < 700:
        print(f"   ⚠️  Dữ liệu chưa đầy đủ ({count}/709)")
    else:
        print("   ✅ Dữ liệu đã sẵn sàng!")

    print("")
    print("🌐 Khởi động NutriAI Backend...")
    print("=" * 60)


if __name__ == "__main__":
    main()

    # Import uvicorn sau khi seed xong
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
