import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from sqlalchemy import text

def clean_database_data():
    db = SessionLocal()
    print("\n" + "="*60)
    print("🧹 ĐANG DỌN DẸP DỮ LIỆU (GIỮ NGUYÊN BẢNG)...")
    print("="*60)
    
    try:
        # Tắt kiểm tra khóa ngoại để xóa không bị lỗi ràng buộc
        db.execute(text("SET session_replication_role = 'replica';"))
        
        # Danh sách các bảng cần xóa dữ liệu (Theo thứ tự từ bảng nối đến bảng gốc)
        tables = [
            "recipe_ingredients",
            "recipe_favorites",
            "food_servings",
            "recipes",
            "foods",
            "users",
            "food_logs",
            "food_servings",
            "meal_plans",
            "meal_plan_items",
            "user_profiles",
            "user_goals",
            "weight_logs"
        ]
        
        for table in tables:
            print(f"Emptying table: {table}...")
            # TRUNCATE giúp xóa sạch và RESET lại ID tự tăng về 1
            db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
        
        # Bật lại kiểm tra khóa ngoại
        db.execute(text("SET session_replication_role = 'origin';"))
        
        db.commit()
        print("\n✅ Đã xóa sạch dữ liệu! Các bảng hiện tại đã trống.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi khi dọn dẹp: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("Xác nhận xóa TẤT CẢ dữ liệu (y/n)? ")
    if confirm.lower() == 'y':
        clean_database_data()
    else:
        print("Đã hủy.")