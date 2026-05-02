import os
import sqlalchemy as sa
from sqlalchemy import inspect

if os.getenv("BACKEND_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.getenv("BACKEND_DATABASE_URL")

from app.database import engine

def check_comprehensive():
    inspector = sa.inspect(engine)
    all_tables = inspector.get_table_names()
    
    print(f"\n🚀 BẮT ĐẦU KIỂM TRA TOÀN DIỆN DATABASE")
    print(f"==========================================")
    print(f"📊 Tổng số bảng phát hiện: {len(all_tables)}")
    print(f"📋 Danh sách: {', '.join(all_tables)}")
    print(f"------------------------------------------\n")

    # Danh sách các bảng quan trọng cần kiểm tra kỹ
    target_tables = [
        'users', 'foods', 'food_servings', 'food_logs', 
        'weight_logs', 'user_goals', 'user_profiles', 
        'recipes', 'recipe_ingredients', 'recipe_favorites'
    ]

    for table in target_tables:
        if table not in all_tables:
            print(f"❌ BẢNG THIẾU: {table}")
            continue

        print(f"🔍 Đang kiểm tra bảng: [{table}]")
        
        # 1. Kiểm tra Cột & Soft Delete
        columns = inspector.get_columns(table)
        col_names = [c['name'] for c in columns]
        
        # Check Soft Delete
        has_is_deleted = 'is_deleted' in col_names
        has_deleted_at = 'deleted_at' in col_names
        
        # Check Timezone cho deleted_at (Rất quan trọng cho Analytics)
        tz_ok = True
        if has_deleted_at:
            col_info = next(c for c in columns if c['name'] == 'deleted_at')
            # Kiểm tra xem có timezone không (Postgres: TIMESTAMP WITH TIME ZONE)
            if not getattr(col_info['type'], 'timezone', False):
                tz_ok = False

        status_sd = "✅ OK" if (has_is_deleted and has_deleted_at and tz_ok) else "❌ LỖI (Thiếu cột hoặc sai Timezone)"
        print(f"   - Soft Delete: {status_sd}")

        # 2. Kiểm tra Index
        indexes = inspector.get_indexes(table)
        idx_names = [i['name'] for i in indexes]
        print(f"   - Indexes ({len(idx_names)}): {idx_names}")

        # Kiểm tra Index đặc biệt của user_goals
        if table == 'user_goals':
            active_goal_idx = next((i for i in indexes if i['name'] == 'one_active_goal_per_user_idx'), None)
            if active_goal_idx:
                where = active_goal_idx.get('dialect_options', {}).get('postgresql_where')
                print(f"   - Index WHERE clause: {where if where else '❌ THIẾU WHERE CLAUSE'}")
            else:
                print(f"   - ❌ THIẾU INDEX: one_active_goal_per_user_idx")

        # 3. Kiểm tra Check Constraints (Dinh dưỡng không được âm)
        check_consts = inspector.get_check_constraints(table)
        if check_consts:
            print(f"   - Constraints: ✅ Đã thiết lập {len(check_consts)} ràng buộc.")
        
        print(f"------------------------------------------")

    print(f"\n✅ KẾT THÚC KIỂM TRA.")

if __name__ == "__main__":
    check_comprehensive()