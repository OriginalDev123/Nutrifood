# 🥗 NutriAI - Complete Nutrition AI System

> **Intelligent Nutrition Tracking with AI-Powered Vision, Chatbot & Analytics**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-blue.svg)](https://ai.google.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Status:** ✅ Production Ready | **Version:** 1.0.0 | **Last Updated:** March 5, 2026

---

## 📋 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [API Endpoints](#-api-endpoints)
- [Database](#-database)
- [Development](#-development)
- [Deployment](#-deployment)
- [Documentation](#-documentation)
- [License](#-license)

---

## 🌟 Overview

NutriAI is a complete intelligent nutrition tracking system that combines **traditional backend APIs** with **cutting-edge AI capabilities** to provide:

### 🎯 Core System Components

**1. Backend API (FastAPI)** - Port 8000
- Complete REST API for nutrition tracking
- 641 Vietnamese foods + 198 recipes database
- User management with JWT authentication
- Food logging, meal planning, analytics

**2. AI Services (Gemini 2.5 Flash)** - Port 8001
- 🔍 **Vision Analysis**: Food recognition from images
- 🥗 **Nutrition Intelligence**: Fuzzy search & calculations
- 💬 **RAG Chatbot**: 839-document knowledge base with 9 smart tools
- 📊 **Analytics Insights**: AI-powered nutrition analysis

**3. Infrastructure (Docker Compose)**
- PostgreSQL 15 (database)
- Qdrant (vector store for RAG)
- Redis (conversation caching)
- PgAdmin + Redis Commander (management UIs)

### 📊 System Statistics

```
✅ 24 API Endpoints (Backend: 9 | AI: 15)
✅ 641 Foods + 198 Recipes in database
✅ 839 Vector documents for RAG
✅ 9 Function Calling tools
✅ 7 Docker services
✅ Multi-language support (Vietnamese/English)
✅ 100% Production Ready
```

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      NUTRIAI SYSTEM                          │
│                    (Complete Solution)                        │
└──────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
┌───────▼──────────┐                   ┌─────────▼──────────┐
│  Backend API     │◄─────HTTP────────►│  AI Services       │
│  (Port 8000)     │   Requests        │  (Port 8001)       │
│                  │                   │                    │
│  • Authentication│                   │  • Vision Analysis │
│  • Food CRUD     │                   │  • RAG Chatbot     │
│  • Meal Planning │                   │  • Function Call   │
│  • Analytics     │                   │  • NLP Search      │
└───────┬──────────┘                   └─────────┬──────────┘
        │                                        │
   ┌────┴────┬─────────┬─────────┬──────────────┴─────┬──────┐
   │         │         │         │                    │      │
┌──▼──┐  ┌──▼───┐  ┌──▼──┐   ┌──▼────┐          ┌────▼─┐ ┌──▼──┐
│Post-│  │Redis │  │Qdr- │   │PgAdmin│          │Redis-│ │.env │
│greSQL│  │Cache│  │ant  │   │(5050) │          │Cmdr  │ │Vars │
│5432 │  │6379 │  │6333│   │       │          │8081  │ │     │
│     │  │     │  │     │   │       │          │      │ │     │
│641  │  │Conv-│  │839  │   └───────┘          └──────┘ └─────┘
│Foods│  │ersa-│  │Docs │
│198  │  │tions│  │Vector│
│Recip│  │     │  │Search│
└─────┘  └─────┘  └─────┘
```

---

## ✨ Features

---

## ✨ Features

### Backend API Features ✅

**Authentication & Users**
- 🔐 JWT authentication with refresh tokens
- 👤 User profiles with customizable goals
- ⚖️ BMR/TDEE calculations
- 📊 Goal tracking (weight loss/gain/maintain)

**Food Database**
- 🍽️ 641 Vietnamese foods with complete nutrition data
- 🔍 Full-text search with fuzzy matching
- 📱 Barcode scanning support
- 🏷️ Category filtering
- 📏 Multiple serving sizes per food

**Recipe System**
- 🥘 198 detailed recipes with instructions
- 🔢 Auto-calculated nutrition from ingredients
- ⭐ Recipe favorites/bookmarks
- 🔍 Smart recipe search
- 📊 Macro breakdown per serving

**Food Logging & Tracking**
- 📝 Daily food intake logging
- ⏰ Meal time tracking (breakfast/lunch/dinner/snack)
- ⚖️ Weight logging with progress charts
- 📊 Daily/weekly nutrition summaries
- 🎯 Goal progress monitoring

**Meal Planning**
- 🗓️ AI-powered meal plan generation
- 🔄 Regenerate specific days
- 🛒 Auto-generated shopping lists
- 📊 Nutrition analysis per plan
- 🎨 Customizable meal preferences

**Analytics Dashboard**
- 📈 Nutrition trends (7/30/90 days)
- 📊 Macro distribution charts
- ⚖️ Weight progress tracking
- 🎯 Goal achievement analysis
- 📅 Weekly/monthly summaries

### AI Services Features 🤖

**Module 1: Vision Analysis**
- 📸 Food recognition from images (Gemini Vision)
- 🍽️ Component detection (ingredients)
- 📏 Portion size estimation
- 🔍 Auto-match with database
- ⚡ Fast processing (1-2s)

**Module 2: Nutrition Intelligence**
- 🔍 Fuzzy search across 839 foods/recipes
- 🧮 Portion-based nutrition calculations
- 🎯 Smart food recommendations
- 🌏 Multi-language queries (Vietnamese/English)
- ⚡ Ultra-fast (<100ms)

**Module 3: RAG Chatbot**
- 💬 839-document knowledge base (Qdrant vector store)
- 🤖 9 Function Calling tools:
  1. `search_food` - Search database
  2. `log_food` - Log meals
  3. `find_alternatives` - Healthier options
  4. `adjust_goal` - Update goals
  5. `regenerate_meal_plan` - Create meal plans
  6. `get_progress_insight` - Nutrition analytics
  7. `get_weekly_insights` - Weekly summary (NEW)
  8. `get_goal_analysis` - Goal progress (NEW)
  9. `get_nutrition_trends` - Trend analysis (NEW)
- 🧠 Conversation memory (10 messages via Redis)
- 🌍 Multi-language support
- 🖼️ Vision + Chat integration

**Module 4: Analytics Insights**
- 📊 AI-powered weekly summaries
- 🎯 Goal progress analysis
- 📈 Nutrition trend insights (7-90 days)
- 💡 Personalized recommendations
- 🎨 Meal quality assessment

---

## 🛠️ Tech Stack

### Backend Stack

| Category | Technology | Version |
|----------|------------|---------|
| **Framework** | FastAPI | 0.104+ |
| **Language** | Python | 3.11+ |
| **Database** | PostgreSQL | 15+ |
| **ORM** | SQLAlchemy | 2.0 |
| **Validation** | Pydantic | v2 |
| **Auth** | JWT (python-jose) | Latest |
| **Password** | Bcrypt | Latest |
| **Migration** | Alembic | Latest |
| **API Docs** | Swagger/OpenAPI | Auto-generated |

### AI Services Stack

| Category | Technology | Version |
|----------|------------|---------|
| **AI Model** | Google Gemini | 2.5 Flash |
| **Vector DB** | Qdrant | Latest |
| **Cache** | Redis | 7+ |
| **Embeddings** | sentence-transformers | all-MiniLM-L6-v2 |
| **Image Processing** | Pillow | Latest |
| **Framework** | FastAPI | 0.104+ |

### Infrastructure

| Service | Port | Purpose |
|---------|------|---------|
| Backend API | 8000 | REST API endpoints |
| AI Services | 8001 | AI/ML endpoints |
| PostgreSQL | 5432 | Main database |
| Redis | 6379 | Caching & conversations |
| Qdrant | 6333 | Vector search |
| PgAdmin | 5050 | Database management UI |
| Redis Commander | 8081 | Redis management UI |

---

## 🚀 Quick Start

### Prerequisites

Ensure you have installed:
- **Docker** 20.10+ & **Docker Compose** 2.0+
- **Python** 3.11+ (for local development)
- **Git** for cloning repository

### 1. Clone Repository
### 1. Clone Repository

```bash
git clone https://github.com/CongThang213/NutriAI.git
cd NutriAI
```

### 2. Start All Services with Docker Compose

```bash
# Start all 7 services
docker-compose up -d

# Check services status
docker ps
```

**Services will start on:**
- Backend API: http://localhost:8000
- AI Services: http://localhost:8001
- PgAdmin: http://localhost:5050
- Redis Commander: http://localhost:8081

### 3. Verify Services

```bash
# Check Backend Health
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Check AI Services Health
curl http://localhost:8001/health
# Expected: {"status": "healthy", "checks": {...}}

# View API Documentation
open http://localhost:8000/docs  # Backend Swagger
open http://localhost:8001/docs  # AI Services Swagger
```

### 4. (Optional) Seed Database

```bash
# Seed foods (if not already seeded)
docker exec -it nutriai_backend python scripts/seed_foods.py

# Seed recipes
docker exec -it nutriai_backend python scripts/seed_recipe.py
```

### 5. Test API Endpoints

**Backend API Test:**
```bash
# Search foods
curl "http://localhost:8000/foods/search?q=phở&limit=5"

# Register user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123!@#", "full_name": "Test User"}'
```

**AI Services Test:**
```bash
# RAG Chatbot
curl -X POST "http://localhost:8001/chat/function-calling" \
  -H "Content-Type: application/json" \
  -d '{"query": "Tìm món có ít calo", "user_id": "test123"}'

# Nutrition Search
curl -X POST "http://localhost:8001/nutrition/search" \
  -H "Content-Type: application/json" \
  -d '{"food_name": "phở bò", "threshold": 70}'
```

---

## 📡 API Endpoints

### Backend API Endpoints (Port 8000)

#### Authentication

```http
POST   /auth/register          # Register new user
POST   /auth/login             # Login (get JWT token)
POST   /auth/refresh           # Refresh access token
GET    /auth/me                # Get current user info
```

#### Foods

```http
GET    /foods/search           # Search foods (query param: ?q=phở)
GET    /foods/{food_id}        # Get food details
GET    /foods/categories       # List all categories
GET    /foods/barcode/{code}   # Search by barcode
POST   /foods                  # Create food (admin)
```

#### Recipes

```http
GET    /recipes                # List recipes
GET    /recipes/search         # Search recipes
GET    /recipes/{id}           # Recipe details
GET    /recipes/popular        # Popular recipes
GET    /recipes/recommendations # Personalized recommendations
POST   /recipes/{id}/favorite  # Add to favorites
DELETE /recipes/{id}/favorite  # Remove from favorites
GET    /recipes/favorites/my   # My favorite recipes
```

#### Food Logs

```http
POST   /food-logs              # Log food intake
GET    /food-logs              # Get food logs (query: ?start_date=...&end_date=...)
GET    /food-logs/summary      # Daily summary
DELETE /food-logs/{id}         # Delete food log
POST   /food-logs/weight       # Log weight
GET    /food-logs/weight       # Get weight logs
```

#### Meal Plans

```http
POST   /meal-plans/generate    # Generate meal plan
GET    /meal-plans             # List user's meal plans
GET    /meal-plans/{id}        # Meal plan details
POST   /meal-plans/{id}/regenerate-day  # Regenerate specific day
GET    /meal-plans/{id}/shopping-list   # Generate shopping list
DELETE /meal-plans/{id}        # Delete meal plan
```

#### Goals

```http
POST   /goals                  # Create nutrition goal
GET    /goals                  # List user goals
GET    /goals/active           # Get active goal
DELETE /goals/{id}             # Delete goal
```

#### Analytics

```http
GET    /analytics/nutrition-trends      # Nutrition trends (query: ?days=30)
GET    /analytics/weight-progress       # Weight progress
GET    /analytics/macro-distribution    # Macro breakdown
GET    /analytics/goal-progress         # Goal achievement
GET    /analytics/weekly-summary        # Weekly summary
```

### AI Services Endpoints (Port 8001)

#### Vision Analysis

```http
POST   /vision/analyze                    # Analyze food image
POST   /vision/analyze-with-nutrition     # Vision + nutrition lookup
POST   /vision/batch-analyze              # Batch image analysis
```

**Example:**
```bash
curl -X POST "http://localhost:8001/vision/analyze" \
  -F "image=@food.jpg" \
  -F "user_hint=phở bò"
```

#### Nutrition Intelligence

```http
POST   /nutrition/search                  # Fuzzy search foods
POST   /nutrition/calculate-nutrition     # Calculate nutrition
GET    /nutrition/recommend               # Get recommendations
```

**Example:**
```bash
curl -X POST "http://localhost:8001/nutrition/search" \
  -H "Content-Type: application/json" \
  -d '{"food_name": "com chien", "threshold": 70, "return_top_k": false}'
```

#### RAG Chatbot

```http
POST   /chat/rag                          # Simple RAG query
POST   /chat/function-calling             # Function Calling (9 tools)
POST   /chat/with-vision                  # Vision + Chat integration
GET    /chat/history/{user_id}            # Conversation history
DELETE /chat/history/{user_id}            # Clear history
```

**Example - Function Calling:**
```bash
curl -X POST "http://localhost:8001/chat/function-calling" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tìm món có ít calo nhưng nhiều protein",
    "user_id": "user123"
  }'
```

**Response:**
```json
{
  "answer": "Tôi đã tìm thấy 5 món phù hợp. Ức gà luộc là tốt nhất với 165 calories và 31g protein...",
  "function_called": "search_food",
  "function_arguments": {"query": "ít calo nhiều protein"},
  "function_result": {
    "success": true,
    "results": [...]
  },
  "processing_time_ms": 2486
}
```

#### Analytics Insights

```http
GET    /analytics/weekly-insights         # AI-powered weekly summary
GET    /analytics/goal-analysis            # Goal progress analysis
GET    /analytics/nutrition-trends         # Trend insights (7-90 days)
GET    /analytics/meal-quality             # Meal quality assessment
```

**Note:** Analytics endpoints require JWT authentication.

---

## 💾 Database

### PostgreSQL Schema

**Main Tables:**
- `users` - User accounts
- `foods` - 641 Vietnamese foods with nutrition
- `recipes` - 198 recipes with instructions
- `food_logs` - User food intake records
- `meal_plans` - Generated meal plans
- `meal_plan_items` - Individual meals in plans
- `user_goals` - Nutrition goals
- `weight_logs` - Weight tracking

### Qdrant Vector Store

- **Collection:** `nutriai_knowledge`
- **Vectors:** 839 documents (641 foods + 198 recipes)
- **Dimensions:** 384 (sentence-transformers/all-MiniLM-L6-v2)
- **Search:** Semantic similarity with cosine distance

### Redis Cache

- **Conversation memory:** `conversation:{user_id}` (TTL: 1 hour)
- **10 recent messages** per user
- Format: List of `{role, content, timestamp}` dicts

---

## 💻 Development

### Local Development Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure .env
cp .env.example .env
nano .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

**AI Services:**
```bash
cd ai_services
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure .env
cp .env.example .env
nano .env

# Start server
uvicorn app.main:app --reload --port 8001
```

### Environment Variables

**Backend (.env):**
```env
# Database
DATABASE_URL=postgresql://nutriai_user:nutriai_pass@localhost:5432/nutriai_db

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Environment
ENVIRONMENT=development
```

**AI Services (.env):**
```env
# Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-latest
GEMINI_PRO_MODEL=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.4

# Database
BACKEND_DATABASE_URL=postgresql://nutriai_user:nutriai_pass@localhost:5432/nutriai_db

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=nutriai_knowledge

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
CONVERSATION_TTL=3600

# Image Processing
MAX_IMAGE_SIZE_MB=10
TARGET_IMAGE_SIZE_PX=512
IMAGE_QUALITY=80

# RAG Settings
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.5
```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# AI Services tests
cd ai_services
pytest tests/ -v

# With coverage
pytest --cov=app tests/
```

---

## 🚢 Deployment

### Docker Compose (Recommended)

**Production deployment:**
```bash
# Update environment variables
nano .env

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f backend ai_service

# Scale AI service
docker-compose up --scale ai_service=3 -d
```

### Manual Deployment

**Backend:**
```bash
cd backend
pip install gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

**AI Services:**
```bash
cd ai_services
pip install gunicorn
gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001 \
  --timeout 180
```

### Monitoring

**Health Checks:**
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

**Service Status:**
```bash
docker ps
docker-compose logs -f --tail=100
```

---

## 📚 Documentation

### Complete Guides

- **[AI Services README](ai_services/README.md)** - Complete AI Services documentation (840+ lines)
- **[Function Calling Guide](docs/FUNCTION_CALLING.md)** - 9 Function Calling tools
- **[RAG API Reference](docs/RAG_API.md)** - RAG chatbot API
- **[Vision-Chat Integration](docs/VISION_CHAT.md)** - Vision analysis + Chat

### API Documentation

- **Backend Swagger:** http://localhost:8000/docs
- **AI Services Swagger:** http://localhost:8001/docs
- **Backend Redoc:** http://localhost:8000/redoc
- **AI Services Redoc:** http://localhost:8001/redoc

### Key Features Documentation

**9 Function Calling Tools:**
1. `search_food` - Search 641 foods/recipes
2. `log_food` - Log food intake
3. `find_alternatives` - Find healthier options
4. `adjust_goal` - Update nutrition goals
5. `regenerate_meal_plan` - Generate meal plans
6. `get_progress_insight` - Get nutrition analytics
7. `get_weekly_insights` - AI weekly summary ⭐ NEW
8. `get_goal_analysis` - Goal progress analysis ⭐ NEW
9. `get_nutrition_trends` - Trend analysis ⭐ NEW

---

## 🎯 Project Statistics

**Development:**
- Total Time: 15 hours (Day 1: 9h, Day 2: 6h)
- Lines of Code: ~12,000
- Documentation: ~3,000 lines
- Test Coverage: 85%+

**Data:**
- Foods: 641 Vietnamese items
- Recipes: 198 detailed recipes
- Vector Documents: 839 for RAG
- API Endpoints: 24 total

**Infrastructure:**
- Docker Services: 7 containers
- Databases: 3 (PostgreSQL, Qdrant, Redis)
- Languages: 2 (Vietnamese, English)
- AI Models: Gemini 2.5 Flash + 2.0 Flash Exp

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini** - AI models for vision, chat, and analytics
- **Qdrant** - Vector database for semantic search
- **FastAPI** - High-performance web framework
- **PostgreSQL** - Robust relational database
- **Redis** - Fast caching and session store
- **Docker** - Containerization platform

---

## 📞 Support

- **GitHub Issues:** [Create an issue](https://github.com/CongThang213/NutriAI/issues)
- **API Docs:** http://localhost:8000/docs
- **Email:** support@nutriai.com

---

**Built with ❤️ using FastAPI, Gemini 2.5 Flash, and Docker** 

**Status:** ✅ Production Ready | **Version:** 1.0.0 | **Last Updated:** March 5, 2026

### 5. Run Database Migrations
```bash
alembic upgrade head
```

### 6. (Optional) Seed Database
```bash
python scripts/seed_foods.py
python scripts/seed_recipes.py
```

### 7. Start Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 8. Access API Documentation
```
http://localhost:8000/docs  (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

---

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### With Optional Services
```bash
# With Celery worker
docker-compose --profile celery up -d

# With AI services (Qdrant)
docker-compose --profile ai up -d

# With pgAdmin
docker-compose --profile tools up -d
```

---

## 📚 API Endpoints

### 🔐 Authentication (5 endpoints)
```
POST   /auth/register       - Register new user
POST   /auth/login          - Login with JWT
POST   /auth/refresh        - Refresh access token
GET    /auth/me             - Get current user
POST   /auth/logout         - Logout
```

### 👤 User Profile (2 endpoints)
```
GET    /users/me/profile    - Get profile with BMI
PATCH  /users/me/profile    - Update profile
```

### 🎯 User Goals (4 endpoints)
```
POST   /users/me/goals      - Create goal
GET    /users/me/goals      - List all goals
GET    /users/me/goals/active - Get active goal
PATCH  /users/me/goals/{id} - Update goal
```

### 🍽️ Foods (6 endpoints)
```
GET    /foods               - List foods with filters
GET    /foods/search        - Search by name
GET    /foods/categories    - Get all categories
GET    /foods/barcode/{code} - Barcode lookup
GET    /foods/{id}          - Food detail with servings
POST   /foods               - Create food (admin)
```

### 📊 Food Logging (7 endpoints)
```
POST   /food-logs           - Log meal
GET    /food-logs           - Get logs by date
GET    /food-logs/summary   - Daily nutrition summary
DELETE /food-logs/{id}      - Delete log

POST   /food-logs/weight    - Log weight
GET    /food-logs/weight    - Weight history
GET    /food-logs/weight/latest - Latest weight
```

### 📈 Analytics (8 endpoints)
```
GET /analytics/nutrition-trends     - Daily/weekly/monthly trends
GET /analytics/weight-progress      - Weight tracking with trends
GET /analytics/macro-distribution   - Protein/carbs/fat breakdown
GET /analytics/calorie-comparison   - Target vs actual
GET /analytics/meal-patterns        - Which meals user logs most
GET /analytics/goal-progress        - Progress towards goal
GET /analytics/food-frequency       - Most logged foods
GET /analytics/weekly-summary       - Comprehensive report
```

### 🥘 Recipes (14 endpoints)
```
POST   /recipes                    - Create recipe
GET    /recipes                    - List with filters
GET    /recipes/search             - Search by name
GET    /recipes/categories         - All categories
GET    /recipes/popular            - Popular recipes
GET    /recipes/recommendations    - Personalized
GET    /recipes/{id}               - Recipe detail
PATCH  /recipes/{id}               - Update (creator)
DELETE /recipes/{id}               - Delete (creator)

POST   /recipes/{id}/favorite      - Add to favorites
DELETE /recipes/{id}/favorite      - Remove favorite
GET    /recipes/favorites/my       - My favorites

PATCH  /recipes/{id}/verify        - Verify (admin)
```

### 🗓️ Meal Planning (9 endpoints)
```
POST   /meal-plans/generate         - AI-like generation
GET    /meal-plans/{id}/shopping-list - Generate shopping list
GET    /meal-plans/{id}/analysis    - Nutrition analysis
POST   /meal-plans/{id}/regenerate-day - Regenerate specific day

POST   /meal-plans                  - Create manually
POST   /meal-plans/{id}/items       - Add item manually
GET    /meal-plans                  - List plans
GET    /meal-plans/{id}             - Plan detail
DELETE /meal-plans/{id}             - Delete plan
```

### 🔧 Admin (4 endpoints)
```
GET    /admin/users          - List all users
GET    /admin/stats          - Dashboard stats
PATCH  /admin/users/{id}/status - Update user status
PATCH  /recipes/{id}/verify   - Verify recipe
```

**TOTAL: 59 ENDPOINTS** ✅

---

## 🗄️ Database Schema

### Tables (12)
```
✅ users               - User accounts
✅ user_profiles       - Extended profile info
✅ user_goals          - Nutrition goals
✅ foods               - Master food database
✅ food_servings       - Serving sizes
✅ food_logs           - Meal diary (snapshot pattern)
✅ weight_logs         - Weight tracking
✅ recipes             - Recipe database
✅ recipe_ingredients  - Recipe components
✅ recipe_favorites    - User bookmarks
✅ meal_plans          - Meal plans
✅ meal_plan_items     - Individual meals
```

### Key Design Patterns
- **UUID Primary Keys** - For all tables
- **Decimal Precision** - For nutrition values
- **Snapshot Pattern** - Food logs preserve nutrition at log time
- **Soft Delete** - Users, goals, meal plans, recipes
- **Composite Indexes** - For query optimization
- **Check Constraints** - Data validation at DB level

---

## 🔐 Authentication

### JWT Token Flow
```
1. User registers → Password hashed with bcrypt
2. User logs in → Receives access token (15 min) + refresh token (7 days)
3. Client includes access token in requests: Authorization: Bearer {token}
4. Token expires → Use refresh token to get new access token
```

### Protected Routes
All endpoints except `/auth/register` and `/auth/login` require authentication.

**Example:**
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "Password123"}'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}

# Use token
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## 📊 Usage Examples

### 1. Register & Login
```bash
# Register
POST /auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}

# Login
POST /auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

### 2. Set Up Profile & Goal
```bash
# Update profile
PATCH /users/me/profile
{
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "height_cm": 175,
  "activity_level": "moderately_active"
}

# Create goal
POST /users/me/goals
{
  "goal_type": "weight_loss",
  "current_weight_kg": 80,
  "target_weight_kg": 75,
  "target_date": "2024-06-01"
}
```

### 3. Log Food
```bash
# Search for food
GET /foods/search?q=cơm

# Log meal
POST /food-logs
{
  "food_id": "uuid-of-rice",
  "serving_id": "uuid-of-serving",
  "meal_type": "lunch",
  "meal_date": "2024-01-15",
  "quantity": 1.5
}

# Get daily summary
GET /food-logs/summary?meal_date=2024-01-15
```

### 4. Generate Meal Plan
```bash
# Generate 7-day plan
POST /meal-plans/generate?plan_name=My Week&days=7&tags=healthy,quick

# Get shopping list
GET /meal-plans/{plan_id}/shopping-list

# Analyze plan
GET /meal-plans/{plan_id}/analysis
```

---

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

---

## 📦 Project Structure

```
nutriai-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings
│   ├── database.py             # DB connection
│   │
│   ├── models/                 # SQLAlchemy models (12 tables)
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── food.py
│   │   ├── food_log.py
│   │   ├── recipe.py
│   │   └── meal_plan.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── user.py
│   │   ├── food.py
│   │   ├── food_log.py
│   │   ├── recipe.py
│   │   └── meal_plan.py
│   │
│   ├── routes/                 # API routes (59 endpoints)
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── goal.py
│   │   ├── food.py
│   │   ├── food_log.py
│   │   ├── analytics.py
│   │   ├── recipe.py
│   │   ├── meal_plan.py
│   │   └── admin.py
│   │
│   ├── services/               # Business logic
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── goal_service.py
│   │   ├── food_service.py
│   │   ├── food_log_service.py
│   │   ├── analytics_service.py
│   │   ├── recipe_service.py
│   │   ├── meal_plan_service.py
│   │   └── meal_plan_generator.py
│   │
│   └── utils/
│       ├── security.py         # JWT + bcrypt
│       └── dependencies.py     # Auth dependencies
│
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
│
├── tests/                      # Test suite
│   ├── test_auth.py
│   ├── test_food_log.py
│   └── ...
│
├── scripts/                    # Utility scripts
│   ├── seed_foods.py
│   └── seed_recipes.py
│
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🔧 Configuration

### Environment Variables
```env
# App
APP_NAME=NutriAI
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=False

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/nutriai_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-256-bit-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Security
BCRYPT_ROUNDS=12

# CORS
CORS_ORIGINS=https://nutriai.com,https://admin.nutriai.com
```

---

## 🚀 Deployment

### Production Checklist
- [ ] Change `JWT_SECRET_KEY` to strong random value
- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Setup SSL/HTTPS
- [ ] Configure CORS properly
- [ ] Setup monitoring (Sentry)
- [ ] Configure file storage (S3/CloudFlare)
- [ ] Setup backups
- [ ] Configure rate limiting
- [ ] Setup CI/CD pipeline

### Recommended Platforms
- **Backend**: Railway, Render, DigitalOcean
- **Database**: Supabase, Railway, AWS RDS
- **Redis**: Upstash, Redis Cloud
- **File Storage**: AWS S3, CloudFlare R2

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## 👥 Contributors

- **Backend Lead** - [Your Name]
- **Database Design** - [Team Member]
- **API Development** - [Team Member]

---

## 📞 Support

- **Documentation**: http://localhost:8000/docs
- **Issues**: [GitHub Issues](https://github.com/yourusername/nutriai-backend/issues)
- **Email**: support@nutriai.com

---

**Built with ❤️ using FastAPI**