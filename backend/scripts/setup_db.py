"""
NutriAI - Database Setup Helper
Kiểm tra và seed dữ liệu thực phẩm vào cơ sở dữ liệu

Chạy: python scripts/setup_db.py
"""

import sys
from pathlib import Path

# Thiết lập path để import module từ thư mục gốc
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.food import Food, FoodServing

db = SessionLocal()


def count_foods():
    """Đếm số thực phẩm trong database"""
    count = db.query(Food).count()
    return count


def count_food_servings():
    """Đếm số food servings trong database"""
    count = db.query(FoodServing).count()
    return count


def seed_foods():
    """Seed dữ liệu thực phẩm"""
    print("\n" + "=" * 70)
    print("🚀 BẮT ĐẦU SEED DỮ LIỆU THỰC PHẨM...")
    print("=" * 70)

    # Import seed data
    from scripts.seed_foods import FOODS_DATA

    count_success = 0
    count_skip = 0
    count_error = 0

    for data in FOODS_DATA:
        # Check if food already exists
        existing = db.query(Food).filter(
            Food.name_vi == data['name_vi']
        ).first()

        if existing:
            count_skip += 1
            print(f"⏭️  Bỏ qua (đã tồn tại): {data['name_vi']}")
            continue

        try:
            # Create food without servings first
            food_data = {k: v for k, v in data.items() if k != 'servings'}
            food = Food(**food_data)
            db.add(food)
            db.flush()

            # Create servings
            servings_data = data.get('servings', [])
            for idx, s in enumerate(servings_data):
                serving = FoodServing(
                    food_id=food.food_id,
                    description=s['description'],
                    serving_size_g=s['size_g'],
                    is_default=s.get('is_default', idx == 0)
                )
                db.add(serving)

            db.commit()
            count_success += 1
            print(f"✅ Đã nạp: {data['name_vi']}")

        except Exception as e:
            db.rollback()
            print(f"❌ Lỗi tại món {data.get('name_vi', 'Unknown')}: {str(e)}")
            count_error += 1

    print("-" * 70)
    print(f"📊 TỔNG KẾT: Thành công: {count_success} | Bỏ qua: {count_skip} | Lỗi: {count_error}")
    print("=" * 70)


def seed_food_servings():
    """Seed food servings cho các món đã có trong DB nhưng chưa có serving"""
    print("\n" + "=" * 70)
    print("🚀 SEED FOOD SERVINGS...")
    print("=" * 70)

    from scripts.seed_foods import FOODS_DATA

    count_success = 0
    count_skip = 0

    for data in FOODS_DATA:
        # Find the food
        food = db.query(Food).filter(
            Food.name_vi == data['name_vi']
        ).first()

        if not food:
            continue

        # Check if food already has servings
        existing_servings = db.query(FoodServing).filter(
            FoodServing.food_id == food.food_id
        ).count()

        if existing_servings > 0:
            count_skip += 1
            continue

        # Add servings
        servings_data = data.get('servings', [])
        for idx, s in enumerate(servings_data):
            serving = FoodServing(
                food_id=food.food_id,
                description=s['description'],
                serving_size_g=s['size_g'],
                is_default=s.get('is_default', idx == 0)
            )
            db.add(serving)

        try:
            db.commit()
            count_success += 1
            print(f"✅ Đã thêm serving cho: {data['name_vi']}")
        except Exception as e:
            db.rollback()
            print(f"❌ Lỗi tại {data['name_vi']}: {str(e)}")

    print("-" * 70)
    print(f"📊 TỔNG KẾT: Thành công: {count_success} | Bỏ qua: {count_skip}")
    print("=" * 70)


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("🍎 NUTRIAI - DATABASE SETUP UTILITY")
    print("=" * 70)

    # Check current state
    food_count = count_foods()
    serving_count = count_food_servings()

    print(f"\n📊 TRẠNG THÁI HIỆN TẠI:")
    print(f"   - Thực phẩm (foods): {food_count}")
    print(f"   - Định lượng (servings): {serving_count}")

    if food_count == 0:
        print("\n⚠️  Database trống hoàn toàn!")
        response = input("\n🤔 Bạn có muốn seed dữ liệu thực phẩm không? (y/n): ").strip().lower()
        if response == 'y':
            seed_foods()
            # Check if servings were also added
            new_serving_count = count_food_servings()
            if new_serving_count == 0:
                seed_food_servings()
        else:
            print("❌ Đã hủy. Vui lòng chạy lại script sau khi có dữ liệu.")
    elif food_count > 0 and serving_count == 0:
        print("\n⚠️  Thực phẩm đã có nhưng chưa có định lượng!")
        response = input("\n🤔 Bạn có muốn seed servings không? (y/n): ").strip().lower()
        if response == 'y':
            seed_food_servings()
    elif food_count >= 700:
        print(f"\n✅ Database đã có đủ dữ liệu ({food_count} thực phẩm). Không cần seed thêm.")
    else:
        print(f"\n⚠️  Database có {food_count} thực phẩm (ít hơn 700).")
        response = input("\n🤔 Bạn có muốn seed thêm không? (y/n): ").strip().lower()
        if response == 'y':
            seed_foods()
            seed_food_servings()

    # Final summary
    print("\n" + "=" * 70)
    print("📊 TRẠNG THÁI CUỐI CÙNG:")
    print(f"   - Thực phẩm (foods): {count_foods()}")
    print(f"   - Định lượng (servings): {count_food_servings()}")
    print("=" * 70)
    print("\n💡 Để seed dữ liệu tự động, chạy: python scripts/setup_db.py --auto")
    print("=" * 70)

    db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NutriAI Database Setup")
    parser.add_argument('--auto', action='store_true', help='Tự động seed mà không hỏi')
    parser.add_argument('--foods-only', action='store_true', help='Chỉ seed foods')
    parser.add_argument('--servings-only', action='store_true', help='Chỉ seed servings')
    args = parser.parse_args()

    if args.foods_only:
        seed_foods()
    elif args.servings_only:
        seed_food_servings()
    elif args.auto:
        if count_foods() == 0:
            seed_foods()
        seed_food_servings()
        print("\n✅ Setup hoàn tất!")
    else:
        main()
