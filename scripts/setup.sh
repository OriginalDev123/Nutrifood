#!/bin/bash
# ============================================
# DOCKER QUICK START SCRIPT
# ============================================

set -e  # Exit on error

echo "==================================="
echo "🐳 NutriAI Docker Setup"
echo "==================================="

# ============================================
# 1. CHECK PREREQUISITES
# ============================================

echo ""
echo "Step 1: Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker daemon is running"

# ============================================
# 2. CREATE .env FILE
# ============================================

echo ""
echo "Step 2: Setting up environment variables..."

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    rm .env.bak 2>/dev/null || true
    
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env and add your API keys (OpenAI, AWS, etc.)"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to abort and edit .env..."
else
    echo "✅ .env file already exists"
fi

# ============================================
# 3. CREATE NECESSARY DIRECTORIES
# ============================================

echo ""
echo "Step 3: Creating directories..."

mkdir -p backend/uploads
mkdir -p backend/logs
mkdir -p backend/init-scripts
mkdir -p models

echo "✅ Created necessary directories"

# ============================================
# 4. PULL DOCKER IMAGES
# ============================================

echo ""
echo "Step 4: Pulling Docker images..."
echo "This may take a few minutes on first run..."

docker compose pull

echo "✅ Docker images pulled"

# ============================================
# 5. BUILD CUSTOM IMAGES
# ============================================

echo ""
echo "Step 5: Building custom Docker images..."

docker compose build

echo "✅ Custom images built"

# ============================================
# 6. START SERVICES
# ============================================

echo ""
echo "Step 6: Starting services..."

docker compose up -d

echo "✅ Services started"

# ============================================
# 7. WAIT FOR SERVICES TO BE HEALTHY
# ============================================

echo ""
echo "Step 7: Waiting for services to be ready..."

# Wait for PostgreSQL
echo -n "Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U nutriai_user > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " ✅"

# Wait for Redis
echo -n "Waiting for Redis..."
until docker compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " ✅"

# Wait for Backend API
echo -n "Waiting for Backend API..."
until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " ✅"

# ============================================
# 8. RUN DATABASE MIGRATIONS
# ============================================

echo ""
echo "Step 8: Running database migrations..."

docker compose exec backend alembic upgrade head

echo "✅ Database migrations completed"

# ============================================
# 9. SEED INITIAL DATA (Optional)
# ============================================

echo ""
read -p "Do you want to seed the database with sample data? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Seeding database..."
    docker compose exec backend python scripts/seed_data.py
    echo "✅ Database seeded"
fi

# ============================================
# 10. DISPLAY STATUS
# ============================================

echo ""
echo "==================================="
echo "✅ Setup Complete!"
echo "==================================="
echo ""
echo "Services running:"
echo "- Backend API:     http://localhost:8000"
echo "- API Docs:        http://localhost:8000/docs"
echo "- PostgreSQL:      localhost:5432"
echo "- Redis:           localhost:6379"
echo "- PgAdmin:         http://localhost:5050"
echo "- Redis Commander: http://localhost:8081"
echo ""
echo "Database credentials:"
echo "- Database: nutriai_db"
echo "- User: nutriai_user"
echo "- Password: (check .env file)"
echo ""
echo "Useful commands:"
echo "- View logs:       docker compose logs -f"
echo "- Stop services:   docker compose down"
echo "- Restart:         docker compose restart"
echo "- View status:     docker compose ps"
echo ""
echo "==================================="

# ============================================
# 11. OPEN SERVICES IN BROWSER (Optional)
# ============================================

read -p "Do you want to open API docs in browser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Detect OS and open browser
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:8000/docs
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open http://localhost:8000/docs
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        start http://localhost:8000/docs
    fi
fi