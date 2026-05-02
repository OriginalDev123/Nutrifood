#!/bin/bash
# NutriAI - Entrypoint Script
# Chạy khi container backend khởi động

set -e

echo "=========================================="
echo "🍎 NutriAI Backend Starting..."
echo "=========================================="

# ==========================================
# BƯỚC 1: Chờ PostgreSQL sẵn sàng
# ==========================================
echo "📦 Đang chờ PostgreSQL..."

# Lấy DATABASE_URL từ biến môi trường
DB_HOST=$(echo $DATABASE_URL | sed -E 's|.*@([^/]+)/.*|\1|' | cut -d':' -f1)
DB_PORT=$(echo $DATABASE_URL | sed -E 's|.*@([^/]+)/.*|\1|' | cut -d':' -f2)
DB_NAME=$(echo $DATABASE_URL | sed -E 's|.*/(.+)|\1|' | cut -d'?' -f1)

# Nếu không có port, mặc định là 5432
if [[ ! "$DB_HOST" == *":"* ]]; then
    DB_PORT=5432
fi

# Đợi cho đến khi PostgreSQL sẵn sàng
until PGPASSWORD=${POSTGRES_PASSWORD:-nutriai_pass_dev} psql -h "$DB_HOST" -p "$DB_PORT" -U nutriai_user -d "$DB_NAME" -c '\q' 2>/dev/null; do
    echo "   ⏳ PostgreSQL chưa sẵn sàng, đang đợi..."
    sleep 2
done

echo "   ✅ PostgreSQL đã sẵn sàng!"


# ==========================================
# BƯỚC 2: Kiểm tra và seed dữ liệu
# ==========================================
echo ""
echo "📊 Đang kiểm tra dữ liệu..."

# Chạy kiểm tra bằng Python (chỉ check, không seed tự động trong container)
python -c "
import sys
from pathlib import Path
sys.path.append('/app')

from app.database import SessionLocal
from app.models.food import Food

db = SessionLocal()
count = db.query(Food).count()
print(f'   📊 Số thực phẩm trong DB: {count}')

if count == 0:
    print('   ⚠️  Database trống! Đang seed dữ liệu...')
    db.close()
    sys.exit(1)  # Sẽ được xử lý bên dưới
elif count < 700:
    print('   ⚠️  Dữ liệu chưa đầy đủ!')
    db.close()
    sys.exit(1)
else:
    print('   ✅ Dữ liệu đã sẵn sàng!')
    db.close()
    sys.exit(0)
" 2>/dev/null

SEED_STATUS=$?

if [ $SEED_STATUS -eq 1 ]; then
    echo ""
    echo "🚀 Bắt đầu seed dữ liệu thực phẩm (709 món)..."

    # Seed foods
    python -c "
import sys
from pathlib import Path
sys.path.append('/app')

from app.database import SessionLocal
from app.models.food import Food, FoodServing
from scripts.seed_foods import FOODS_DATA

db = SessionLocal()
count_success = 0
count_skip = 0

for data in FOODS_DATA:
    existing = db.query(Food).filter(Food.name_vi == data['name_vi']).first()
    if existing:
        count_skip += 1
        continue

    try:
        food_data = {k: v for k, v in data.items() if k != 'servings'}
        food = Food(**food_data)
        db.add(food)
        db.flush()

        for idx, s in enumerate(data.get('servings', [])):
            serving = FoodServing(
                food_id=food.food_id,
                description=s['description'],
                serving_size_g=s['size_g'],
                is_default=s.get('is_default', idx == 0)
            )
            db.add(serving)

        db.commit()
        count_success += 1
        print(f'   ✅ {data[\"name_vi\"]}')
    except Exception as e:
        db.rollback()
        print(f'   ❌ Lỗi: {data[\"name_vi\"]}')

print(f'')
print(f'   📊 Tổng kết: {count_success} thành công, {count_skip} bỏ qua')
db.close()
"

    echo "   ✅ Seed hoàn tất!"
elif [ $SEED_STATUS -eq 0 ]; then
    echo "   ✅ Dữ liệu đã có sẵn trong database"
fi


# ==========================================
# BƯỚC 3: Khởi động Backend
# ==========================================
echo ""
echo "🌐 Khởi động NutriAI Backend..."
echo "=========================================="

exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
