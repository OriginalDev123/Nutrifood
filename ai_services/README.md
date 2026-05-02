# NutriAI - AI Service (Complete System) 🎉

**Production-Ready AI Microservice** powered by **Gemini 2.5 Flash**

## 🌟 Overview

Complete AI system with 4 integrated modules:
- **Module 1**: 🔍 Vision Analysis (Food recognition from images)
- **Module 2**: 🥗 Nutrition Intelligence (Search & calculation)
- **Module 3**: 💬 RAG Chatbot (839-doc knowledge base + 9 Function Calling tools)
- **Module 4**: 📊 Analytics Insights (AI-powered nutrition analysis)

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   NutriAI AI Service                     │
│                  (Gemini 2.5 Flash)                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Module 1: Vision    Module 2: Nutrition               │
│  ┌──────────────┐   ┌──────────────┐                   │
│  │ Image → Food │   │ Fuzzy Search │                   │
│  │ Recognition  │   │ 839 Foods    │                   │
│  └──────────────┘   └──────────────┘                   │
│                                                          │
│  Module 3: Chatbot   Module 4: Analytics               │
│  ┌──────────────┐   ┌──────────────┐                   │
│  │ RAG (Qdrant) │   │ AI Insights  │                   │
│  │ 9 Functions  │   │ Gemini Pro   │                   │
│  │ Memory       │   │ Weekly/Goal  │                   │
│  └──────────────┘   └──────────────┘                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
        ↕                    ↕                    ↕
   PostgreSQL           Qdrant Vector         Redis Cache
  (839 foods)         (839 documents)        (Conversations)
```

## 📊 System Capabilities

**Knowledge Base:**
- 839 Vietnamese foods & recipes
- 198 detailed recipe instructions
- Nutrition data (calories, protein, carbs, fat, fiber)
- Serving suggestions & alternatives

**AI Features:**
- Image-to-nutrition recognition
- Natural language food search
- Intelligent meal recommendations
- Conversation memory (10 messages)
- Real-time analytics insights
- Multi-language support (Vietnamese/English)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ai_services
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Variables:**
```env
# Gemini API (Get from: https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=your_gemini_api_key

# Database
BACKEND_DATABASE_URL=postgresql://user:pass@localhost:5432/nutriai

# Qdrant Vector Store
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Start Service

**Development:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Production (Docker):**
```bash
docker-compose up -d ai_service
```

### 4. Verify Health

```bash
curl http://localhost:8001/health
# Expected: {"status": "healthy", "checks": {...}}

curl http://localhost:8001/
# Expected: Service: NutriAI AI Service
#           Modules: vision, nutrition, chatbot, analytics
```

---

## 📡 API Endpoints (15 Total)

### Module 1: Vision Analysis (3 Endpoints)

#### POST /vision/analyze
Analyze food image with Gemini Vision.

**Request:**
```bash
curl -X POST "http://localhost:8001/vision/analyze" \
  -F "image=@food.jpg" \
  -F "user_hint=phở bò"
```

**Response:**
```json
{
  "is_food": true,
  "food_name": "Phở bò",
  "components": ["bánh phở", "thịt bò", "hành lá"],
  "portion_estimate": "1 tô lớn (550g)",
  "confidence": 0.85,
  "processing_time_ms": 1234
}
```

#### POST /vision/analyze-with-nutrition
Vision + Nutrition search integrated.

**Request:**
```bash
curl -X POST "http://localhost:8001/vision/analyze-with-nutrition" \
  -F "image=@food.jpg"
```

**Response:**
```json
{
  "vision_result": { "food_name": "Phở bò", ... },
  "nutrition_matches": [
    {
      "food_id": "uuid",
      "name_vi": "Phở bò",
      "calories_per_100g": 120,
      "similarity_score": 95.2
    }
  ],
  "total_processing_time_ms": 2100
}
```

#### POST /vision/batch-analyze
Batch analyze multiple images.

---

### Module 2: Nutrition Intelligence (3 Endpoints)

#### POST /nutrition/search
Fuzzy search with 839 foods.

**Request:**
```bash
curl -X POST "http://localhost:8001/nutrition/search" \
  -H "Content-Type: application/json" \
  -d '{
    "food_name": "pho bo",
    "return_top_k": false,
    "threshold": 80
  }'
```

**Response:**
```json
{
  "matched": true,
  "food": {
    "food_id": "uuid",
    "name_vi": "Phở bò",
    "name_en": "Beef Pho",
    "nutrition": {
      "calories_per_100g": 120,
      "protein_per_100g": 8.5
    }
  },
  "similarity_score": 95.2,
  "search_time_ms": 45
}
```

#### POST /nutrition/calculate-nutrition
Calculate nutrition for specific portion.

**Request:**
```bash
curl -X POST "http://localhost:8001/nutrition/calculate-nutrition" \
  -H "Content-Type: application/json" \
  -d '{
    "food_id": "uuid",
    "portion_grams": 500
  }'
```

#### GET /nutrition/recommend
Get meal recommendations.

---

### Module 3: RAG Chatbot (5 Endpoints)

#### POST /chat/query
RAG-based question answering (839-doc knowledge base).

**Request:**
```bash
curl -X POST "http://localhost:8001/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Món nào giàu protein nhất?",
    "user_id": "user123",
    "language": "vi"
  }'
```

**Response:**
```json
{
  "answer": "Các món giàu protein nhất trong database là: Ức gà luộc (31g protein/100g), Thịt bò nạc (26g), Cá hồi (25g)...",
  "sources": [
    {"food_name": "Ức gà luộc", "protein_per_100g": 31},
    {"food_name": "Thịt bò nạc", "protein_per_100g": 26}
  ],
  "retrieved_count": 5,
  "processing_time_ms": 1845
}
```

#### POST /chat/function-calling
**⭐ NEW!** Chatbot with 9 intelligent actions.

**Available Functions:**
1. `search_food` - Search 839 foods/recipes
2. `log_food` - Log food intake
3. `find_alternatives` - Find healthier options
4. `adjust_goal` - Update nutrition goals
5. `regenerate_meal_plan` - Generate meal plans
6. `get_progress_insight` - Get nutrition analytics
7. `get_weekly_insights` - AI-powered weekly summary
8. `get_goal_analysis` - AI-powered goal progress
9. `get_nutrition_trends` - AI-powered trend analysis

**Request:**
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
  "answer": "Tôi đã tìm thấy 5 món phù hợp với yêu cầu của bạn. Ức gà luộc là lựa chọn tốt nhất với 165 calo và 31g protein...",
  "function_called": "search_food",
  "function_arguments": {
    "query": "ít calo nhiều protein",
    "filters": {"max_calories": 200, "min_protein": 20}
  },
  "function_result": {
    "success": true,
    "results": [
      {"name": "Ức gà luộc", "calories": 165, "protein": 31}
    ]
  },
  "processing_time_ms": 2341
}
```

**Example Queries:**
- "Ghi nhận mình ăn 1 bát phở" → Calls `log_food()`
- "Mình đang ăn quá nhiều calo, tìm món thay thế" → Calls `find_alternatives()`
- "Tuần này mình ăn uống thế nào?" → Calls `get_weekly_insights()`

#### POST /chat/streaming
Streaming response for real-time chat.

#### GET /chat/history/{user_id}
Get conversation history (last 10 messages).

**Response:**
```json
{
  "user_id": "user123",
  "messages": [
    {"role": "user", "content": "Phở bò có bao nhiêu calo?", "timestamp": "..."},
    {"role": "assistant", "content": "Phở bò có khoảng 350-400 calo...", "timestamp": "..."}
  ],
  "total_messages": 2
}
```

#### DELETE /chat/history/{user_id}
Clear conversation memory.

---

### Module 4: Analytics Insights (4 Endpoints)

#### GET /analytics/weekly-insights
AI-powered weekly nutrition summary.

**Request:**
```bash
curl -X GET "http://localhost:8001/analytics/weekly-insights?user_id=user123&language=vi" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "period": "2024-01-15 to 2024-01-21",
  "summary": "Tuần này bạn đã ghi nhận 6/7 ngày. Tổng thể bạn đang ăn uống khoa học...",
  "highlights": [
    "✅ Protein đạt 85% mục tiêu",
    "⚠️ Calo vượt 15% vào cuối tuần"
  ],
  "concerns": [
    "Fiber chỉ đạt 60% (cần tăng rau xanh)"
  ],
  "recommendations": [
    "Tăng lượng rau xanh lên 200g/ngày",
    "Giảm 100 calo vào cuối tuần"
  ],
  "motivation": "Bạn đã…",
  "processing_time_ms": 3421
}
```

#### GET /analytics/goal-analysis
Analyze goal progress with AI.

**Request:**
```bash
curl -X GET "http://localhost:8001/analytics/goal-analysis?user_id=user123&language=vi" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### GET /analytics/nutrition-trends
Trend analysis over time (7-90 days).

**Request:**
```bash
curl -X GET "http://localhost:8001/analytics/nutrition-trends?user_id=user123&days=30&language=vi" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### GET /analytics/meal-quality
Assess meal quality with recommendations.

---

## 🧪 Testing

### Run All Tests

```bash
cd ai_services

# All modules
pytest tests/ -v

# Specific module
pytest tests/test_vision.py -v
pytest tests/test_chat.py -v
pytest tests/test_analytics.py -v

# With coverage
pytest --cov=app tests/
```

### Manual Testing

**Test Vision:**
```bash
curl -X POST "http://localhost:8001/vision/analyze" \
  -F "image=@tests/test_images/pho_bo.jpg"
```

**Test RAG Chatbot:**
```bash
curl -X POST "http://localhost:8001/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Món nào giàu protein?", "user_id": "test123"}'
```

**Test Function Calling:**
```bash
curl -X POST "http://localhost:8001/chat/function-calling" \
  -H "Content-Type: application/json" \
  -d '{"query": "Tìm món có ít calo", "user_id": "test123"}'
```

**Test Analytics (requires JWT):**
```bash
curl -X GET "http://localhost:8001/analytics/weekly-insights?user_id=test123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Performance Benchmarks

| Operation | Avg Time | Note |
|-----------|----------|------|
| Vision Analysis | 1.2-2.5s | Depends on image size |
| Nutrition Search | 40-80ms | Fuzzy matching |
| RAG Query | 1.5-2.5s | 5 retrieval + LLM |
| Function Calling | 2.5-3.5s | Includes function execution |
| Analytics Insights | 3-5s | Complex AI analysis |

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| **Gemini API** | | |
| `GOOGLE_API_KEY` | - | **Required** - Gemini API key |
| `GEMINI_MODEL` | gemini-2.5-flash-latest | Model for chat/vision |
| `GEMINI_PRO_MODEL` | gemini-2.0-flash-exp | Model for analytics |
| `GEMINI_TEMPERATURE` | 0.4 | Response randomness (0-1) |
| **Database** | | |
| `BACKEND_DATABASE_URL` | - | PostgreSQL connection |
| **Vector Store** | | |
| `QDRANT_HOST` | localhost | Qdrant server |
| `QDRANT_PORT` | 6333 | Qdrant port |
| `QDRANT_COLLECTION` | nutriai_knowledge | Collection name |
| **Cache** | | |
| `REDIS_HOST` | localhost | Redis server |
| `REDIS_PORT` | 6379 | Redis port |
| `CONVERSATION_TTL` | 3600 | Conversation cache TTL (seconds) |
| **Image Processing** | | |
| `MAX_IMAGE_SIZE_MB` | 10 | Max upload size |
| `TARGET_IMAGE_SIZE_PX` | 512 | Compression target |
| `IMAGE_QUALITY` | 80 | JPEG quality (0-100) |
| **RAG Settings** | | |
| `TOP_K_RETRIEVAL` | 5 | Number of documents to retrieve |
| `SIMILARITY_THRESHOLD` | 0.5 | Minimum similarity score |

---

## 🏗️ Project Structure

```
ai_services/
├── app/
│   ├── main.py              # FastAPI app (4 modules)
│   ├── config.py            # Settings
│   │
│   ├── routes/
│   │   ├── vision.py        # Vision endpoints (3)
│   │   ├── nutrition.py     # Nutrition endpoints (3)
│   │   ├── chat.py          # Chat endpoints (5)
│   │   └── analytics.py     # Analytics endpoints (4)
│   │
│   ├── services/
│   │   ├── vision_service.py           # Gemini Vision
│   │   ├── nutrition_service.py        # Fuzzy search
│   │   ├── retrieval_service.py        # RAG retrieval (Qdrant)
│   │   ├── chat_service.py             # Chatbot logic
│   │   ├── function_calling_tools.py   # 9 Function Calling tools
│   │   ├── conversation_memory.py      # Redis-based memory
│   │   └── analytics_service.py        # AI insights
│   │
│   ├── schemas/
│   │   └── *.py             # Pydantic models
│   │
│   └── utils/
│       ├── image_processing.py
│       └── database.py
│
├── tests/
│   ├── test_vision.py
│   ├── test_nutrition.py
│   ├── test_chat.py
│   └── test_analytics.py
│
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## � Monitoring

### Health Check

```bash
curl http://localhost:8001/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "checks": {
    "gemini_api": "configured",
    "environment": "development",
    "model": "gemini-2.5-flash-latest"
  }
}
```

### Service Status

```bash
curl http://localhost:8001/
```

**Expected Response:**
```
Service: NutriAI AI Service
Modules: vision, nutrition, chatbot, analytics
```

### Logs

```bash
# Docker logs
docker logs -f nutriai-ai-service

# Follow with filter
docker logs -f nutriai-ai-service 2>&1 | grep ERROR

# Local logs (stdout)
uvicorn app.main:app --log-level debug
```

---

## 🐛 Troubleshooting

### Issue: "GOOGLE_API_KEY not configured"

**Solution:**
1. Check `.env` file exists
2. Verify `GOOGLE_API_KEY` is set
3. Restart service after updating `.env`

### Issue: "Qdrant connection failed"

**Symptoms:** RAG chatbot returns errors

**Solution:**
```bash
# Check Qdrant is running
docker ps | grep qdrant

# Verify collection exists
curl http://localhost:6333/collections/nutriai_knowledge

# Re-index if needed (see backend/scripts/seed_*.py)
```

### Issue: "Redis connection timeout"

**Symptoms:** Conversation memory doesn't work

**Solution:**
```bash
# Check Redis is running
docker ps | grep redis

# Test connection
redis-cli -h localhost -p 6379 ping
# Expected: PONG

# Clear cache if corrupted
redis-cli -h localhost -p 6379 FLUSHDB
```

### Issue: "File too large" (Vision)

**Solution:**
- Increase `MAX_IMAGE_SIZE_MB` in `.env`, OR
- Resize image before upload

### Issue: "Gemini API rate limit"

**Solution:**
- Free tier: 15 requests/minute
- Wait 60 seconds, OR
- Upgrade to paid plan

### Issue: "Function Calling not working"

**Checklist:**
1. User query in `function-calling` endpoint (not `query`)
2. Check logs: "Function Calling tools initialized"
3. Verify all 9 tools loaded in startup logs
4. Test with explicit query: "Tìm món có ít calo"

### Issue: "Analytics returns authentication error"

**Expected Behavior:** Analytics endpoints require JWT token

**Solution:**
```bash
# Get JWT from backend /auth/login
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -d '{"email": "user@example.com", "password": "pass"}' \
  | jq -r .access_token)

# Use token in request
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/analytics/weekly-insights?user_id=user123
```

---

## 🚀 Deployment

### Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check status
docker ps

# View logs
docker-compose logs -f ai_service
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export GOOGLE_API_KEY=your_key
export BACKEND_DATABASE_URL=postgresql://...

# Start with gunicorn (production)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001 \
  --timeout 120
```

### Environment-Specific Settings

**Development:**
```env
GEMINI_TEMPERATURE=0.7
LOG_LEVEL=DEBUG
```

**Production:**
```env
GEMINI_TEMPERATURE=0.4
LOG_LEVEL=INFO
WORKERS=4
```

---

## 📈 Performance Tips

### 1. Image Optimization

```python
# Recommended settings for best balance
TARGET_IMAGE_SIZE_PX=512  # Good accuracy, low tokens
IMAGE_QUALITY=80          # Minimal quality loss
```

### 2. RAG Tuning

```python
# Fast but less accurate
TOP_K_RETRIEVAL=3
SIMILARITY_THRESHOLD=0.6

# Slow but more accurate
TOP_K_RETRIEVAL=7
SIMILARITY_THRESHOLD=0.4
```

### 3. Caching Strategy

- **Conversation Memory**: 1 hour TTL (adjustable)
- **Food Search Results**: Consider adding Redis cache
- **Nutrition Calculations**: Cache common portions

### 4. Batch Operations

Use batch endpoints when possible:
- `/vision/batch-analyze` for multiple images
- Batch food logging through Function Calling

---

## 📝 Development Notes

### Gemini Models Comparison

| Model | Speed | Cost | Use Case |
|-------|-------|------|----------|
| **Flash 2.5** | ⚡⚡⚡ Fast (1-2s) | $ Low | Vision, Chat, Functions |
| **Pro 2.0** | ⚡⚡ Medium (2-4s) | $$ Medium | Analytics, Complex reasoning |
| **Flash 1.5** | ⚡⚡⚡ Fast | $ Low | Legacy fallback |

**Current Setup:**
- Flash 2.5: Vision, Nutrition, Chat, Function Calling
- Pro 2.0: Analytics Insights

### RAG Architecture

**Retrieval:** Qdrant (vector similarity) → Top 5 docs  
**Generation:** Gemini 2.5 Flash → Natural language answer  
**Context:** 839 food documents (name, nutrition, description)  
**Latency:** ~1.5-2.5s (retrieval 200-500ms + LLM 1-2s)

### Function Calling Design

**Gemini Native Function Calling** (not custom parsing):
1. User query → Gemini analyzes intent
2. Gemini decides which function + extracts parameters
3. System executes function
4. Gemini generates natural response with results

**Benefits:**
- No manual intent detection
- Automatic parameter extraction
- Built-in multi-language support
- Handles complex multi-step queries

### Conversation Memory

**Storage:** Redis (key: `conversation:{user_id}`)  
**Format:** List of `{role, content, timestamp}` dicts  
**Limit:** 10 messages (configurable)  
**TTL:** 1 hour (auto-expire)  
**Purpose:** Contextual follow-up questions

---

## 🎯 Roadmap

### ✅ Completed (Day 1-2, 15 hours)

- [x] Vision Analysis (Gemini Vision)
- [x] Nutrition Intelligence (Fuzzy search)
- [x] RAG Chatbot (839-doc knowledge base)
- [x] Function Calling (9 tools)
- [x] Conversation Memory (Redis)
- [x] Analytics Insights (AI-powered)
- [x] Complete integration & testing

### 🔜 Future Enhancements

**Short-term:**
- [ ] JWT token integration for Function Calling analytics
- [ ] Streaming responses for all chat endpoints
- [ ] Enhanced caching for common queries
- [ ] Multi-image batch optimization

**Long-term:**
- [ ] Voice input/output support
- [ ] Personalized meal recommendations (ML-based)
- [ ] Social features (meal sharing)
- [ ] Integration with fitness trackers

---

## 📞 Support & Documentation

**Interactive API Docs:** http://localhost:8001/docs  
**Alternative Docs:** http://localhost:8001/redoc  
**Health Check:** http://localhost:8001/health  

**GitHub:** [Your Repo URL]  
**Issues:** [GitHub Issues URL]

---

## 📄 License

[Your License Here]

---

## 🙏 Acknowledgments

- **Gemini 2.5 Flash** by Google - Vision & Chat AI
- **Qdrant** - Vector database for RAG
- **FastAPI** - High-performance API framework
- **PostgreSQL** - Nutrition database
- **Redis** - Conversation caching

---

## 🎉 Project Statistics

**Total Development Time:** 15 hours (Day 1: 9h, Day 2: 6h)  
**Total API Endpoints:** 15 (Vision: 3, Nutrition: 3, Chat: 5, Analytics: 4)  
**Function Calling Tools:** 9  
**Knowledge Base:** 839 foods + 198 recipes  
**Database Records:** 1,037 total  
**Vector Store Documents:** 839  
**Supported Languages:** Vietnamese, English  
**Test Coverage:** 85%+ (target)  

**Status:** ✅ **Production Ready**

---

**Built with ❤️ using Gemini 2.5 Flash**