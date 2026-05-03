"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError

from app.database import get_db, get_db_info
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import ValidationError

# Brute Force or DoS
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import logging

# Import all routers
from app.routes import auth
from app.routes import food
from app.routes import food_log
from app.routes import user
from app.routes import goal
from app.routes import admin
from app.routes import meal_plan
from app.routes import analytics
from app.routes import uploads
from app.routes import recipe
from app.routes import recommend
from app.routes import health_profile



# Khởi tạo Logger để ghi lại vết lỗi hệ thống
logger = logging.getLogger("uvicorn.error")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    description="""
    NutriAI - Smart Nutrition System for Vietnamese Market
    
    ## Features
    
    * **Authentication**: Register, login, JWT tokens
    * **User Management**: Profile, goals, preferences
    * **Food Database**: 500+ Vietnamese foods, barcode lookup
    * **Food Logging**: Daily meal tracking with nutrition snapshots
    * **Weight Tracking**: Progress monitoring
    * **Admin Panel**: User & food management
    
    ## Authentication
    
    Most endpoints require authentication. After login:
    1. Use the `access_token` from login response
    2. Click "Authorize" button (🔒) at top right
    3. Enter: `Bearer <your_access_token>`
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)


# 1. Khởi tạo limiter dựa trên IP của người gọi
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# 2. Đăng ký handler để xử lý khi người dùng vượt quá số lần gọi cho phép
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==========================================
# GLOBAL EXCEPTION HANDLERS
# ==========================================

@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    """Xử lý lỗi ràng buộc Database (Ví dụ: Trùng email, sai khóa ngoại)"""
    logger.error(f"Database Integrity Error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Xung đột dữ liệu hoặc vi phạm ràng buộc hệ thống.",
            "error_type": "IntegrityError"
        }
    )

@app.exception_handler(OperationalError)
async def operational_exception_handler(request: Request, exc: OperationalError):
    """Xử lý lỗi kết nối Database (Ví dụ: DB bị sập)"""
    logger.critical(f"Database Connection Error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Không thể kết nối đến cơ sở dữ liệu. Vui lòng thử lại sau.",
            "error_type": "OperationalError"
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Xử lý các lỗi logic nghiệp vụ mà chúng ta chủ động raise"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_type": "ValueError"}
    )

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# INCLUDE ROUTERS
# ==========================================

# Public routes
app.include_router(auth.router)

# Protected user routes
app.include_router(user.router)      # User profile
app.include_router(goal.router)      # User goals
app.include_router(health_profile.router)  # Health profile
app.include_router(food.router)      # Food database
app.include_router(food_log.router)  # Food & weight logging
app.include_router(recipe.router)     # Recipe management & matcher (Module 4)
app.include_router(meal_plan.router)  # Meal planning
app.include_router(analytics.router)  # Analytics
app.include_router(uploads.router)   # File uploads
app.include_router(recommend.router) # Food recommendation (Module 3)

# Admin routes
app.include_router(admin.router)


# ==========================================
# HEALTH CHECK ENDPOINTS
# ==========================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check for load balancer"""
    return {"status": "healthy"}


@app.get("/db/info", tags=["Database"])
async def database_info():
    """Get database connection pool info"""
    return get_db_info()


@app.get("/db/test", tags=["Database"])
async def test_database(db: Session = Depends(get_db)):
    """
    Test database connection
    
    This endpoint uses dependency injection:
    - get_db() creates a session
    - Session is injected into db parameter
    - Session is automatically closed after response
    """
    try:
        # Execute a simple query
        result = db.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        
        return {
            "status": "connected",
            "test_query_result": row[0],
            "message": "Database connection is working!"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# ==========================================
# STARTUP/SHUTDOWN EVENTS
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Swagger UI: http://{settings.HOST}:{settings.PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    print(f"Stopping {settings.APP_NAME}...")


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG  # Auto-reload in development
    )