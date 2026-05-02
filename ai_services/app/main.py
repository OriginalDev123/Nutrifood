"""
NutriAI - AI Service
FastAPI Application - Vision Analysis Module
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.config import settings
from app.routes import vision, nutrition, chat, analytics, meal_planning, advice

# === LOGGING CONFIGURATION ===
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === CREATE FASTAPI APP ===
app = FastAPI(
    title="NutriAI - AI Service",
    description="AI-powered food recognition và nutrition analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# === CORS MIDDLEWARE ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === REQUEST LOGGING MIDDLEWARE ===
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log mọi request với timing
    """
    start_time = time.time()
    
    # Log request info
    logger.info(f"➡️  {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Log response
    logger.info(
        f"⬅️  {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {duration_ms}ms"
    )
    
    # Add timing header
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    
    return response


# === ROOT ENDPOINT ===
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint - service info
    """
    return {
        "service": "NutriAI AI Service",
        "version": "1.0.0",
        "status": "operational",
        "modules": ["vision", "nutrition", "chatbot", "analytics", "meal_planning", "advice"],  # Added analytics
        "documentation": "/docs"
    }


# === HEALTH CHECK ===
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint
    
    Verify:
    - Service đang chạy
    - Gemini API key configured
    """
    health_status = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check Gemini API key
    if settings.validate_api_key():
        health_status["checks"]["gemini_api"] = "configured"
    else:
        health_status["status"] = "degraded"
        health_status["checks"]["gemini_api"] = "missing"
    
    # Check environment
    health_status["checks"]["environment"] = settings.ENVIRONMENT
    health_status["checks"]["chat_model"] = settings.GEMINI_MODEL
    health_status["checks"]["vision_model"] = settings.GEMINI_VISION_MODEL or settings.GEMINI_MODEL
    
    return health_status


# === GLOBAL EXCEPTION HANDLER ===
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Xử lý tất cả unhandled exceptions
    """
    logger.error(f"❌ Unhandled exception: {str(exc)}", exc_info=True)
    
    # Chỉ show detail nếu development
    detail = str(exc) if not settings.is_production else "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": detail
        }
    )


# === REGISTER ROUTERS ===
app.include_router(vision.router)
app.include_router(nutrition.router)
app.include_router(chat.router)
app.include_router(analytics.router)  # Task 10: Analytics Insights
app.include_router(meal_planning.router)  # Task: Meal Planning AI
app.include_router(advice.router)  # Nutrition Advice AI


# === STARTUP EVENT ===
@app.on_event("startup")
async def startup_event():
    """
    Chạy khi service khởi động
    """
    logger.info("=" * 60)
    logger.info("🚀 NutriAI AI Service Starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Gemini Chat Model: {settings.GEMINI_MODEL}")
    logger.info(f"Gemini Vision Model: {settings.GEMINI_VISION_MODEL or settings.GEMINI_MODEL}")
    logger.info(f"Max Image Size: {settings.MAX_IMAGE_SIZE_MB}MB")
    logger.info(f"Target Image Size: {settings.TARGET_IMAGE_SIZE_PX}px")
    
    # Validate API key
    if not settings.validate_api_key():
        logger.warning("⚠️  GOOGLE_API_KEY chưa được cấu hình!")
        logger.warning("⚠️  AI Vision sẽ không hoạt động cho đến khi có API key")
    else:
        logger.info("✅ Gemini API key configured")
    
    # Check database connection (Module 2)
    from app.database import check_database_connection
    if check_database_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.warning("⚠️  Database connection failed - Nutrition search unavailable")
    
    # Initialize chat services (Module 6)
    try:
        from app.routes.chat import initialize_chat_services
        initialize_chat_services()
        logger.info("✅ RAG Chatbot services initialized")
    except Exception as e:
        logger.warning(f"⚠️  Chatbot initialization failed: {str(e)}")
        logger.warning("⚠️  Chatbot will be unavailable until Qdrant is running")
    
    logger.info("=" * 60)


# === SHUTDOWN EVENT ===
@app.on_event("shutdown")
async def shutdown_event():
    """
    Chạy khi service shutdown
    """
    logger.info("🛑 NutriAI AI Service shutting down...")


# === RUN APPLICATION ===
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=not settings.is_production,
        log_level=settings.LOG_LEVEL.lower()
    )