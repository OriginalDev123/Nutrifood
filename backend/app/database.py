# app/database.py
"""
Database Connection Management

Concepts:
- Engine: Kết nối đến database, quản lý connection pool
- SessionLocal: Factory để tạo database sessions
- Base: Base class cho tất cả SQLAlchemy models
- get_db(): Dependency injection cho FastAPI routes
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from app.config import settings

# Setup logging
logger = logging.getLogger(__name__)

# ==========================================
# 1. CREATE ENGINE
# ==========================================
"""
Engine là "trái tim" của SQLAlchemy:
- Quản lý connection pool (tái sử dụng connections)
- Execute SQL statements
- Handle transactions

Parameters:
- pool_size: Số connections giữ sẵn (default: 5)
- max_overflow: Số connections thêm khi cần (default: 10)
- pool_pre_ping: Test connection trước khi dùng (tránh stale connections)
- echo: Log tất cả SQL queries (dùng cho debug)
"""

engine = create_engine(
    settings.DATABASE_URL,
    
    # Connection Pool Settings
    poolclass=QueuePool,          # Loại pool (QueuePool = default, tốt nhất)
    pool_size=5,                   # Số connections giữ sẵn
    max_overflow=10,               # Tối đa thêm 10 connections khi busy
    pool_timeout=30,               # Timeout 30s khi chờ connection
    pool_recycle=3600,             # Recycle connection sau 1 giờ
    pool_pre_ping=True,            # Test connection trước khi dùng (QUAN TRỌNG!)
    
    # Logging
    echo=settings.DB_ECHO,         # True = log tất cả SQL (dùng khi debug)
    
    # Performance
    future=True,                   # Use SQLAlchemy 2.0 style
)

# ==========================================
# CONNECTION POOL MONITORING (Optional)
# ==========================================
"""
Đây là advanced feature để monitor connection pool
Giúp debug khi có connection leak
"""

@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log khi có connection mới được tạo"""
    logger.info("Database connection established")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log khi connection được lấy từ pool"""
    logger.debug("Connection checked out from pool")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log khi connection được trả về pool"""
    logger.debug("Connection returned to pool")


# ==========================================
# 2. CREATE SESSION FACTORY
# ==========================================
"""
SessionLocal là factory để tạo database sessions

Session = "transaction scope"
- Mỗi request nên có 1 session riêng
- Session quản lý INSERT/UPDATE/DELETE operations
- Commit hoặc rollback khi xong

Parameters:
- autocommit=False: Phải gọi commit() thủ công (an toàn hơn)
- autoflush=False: Không tự động flush trước query (control tốt hơn)
- bind=engine: Bind với engine đã tạo
"""

SessionLocal = sessionmaker(
    autocommit=False,  # Phải gọi db.commit() thủ công
    autoflush=False,   # Không tự động flush
    bind=engine,       # Kết nối với engine
    expire_on_commit=True,  # Refresh objects sau commit
)


# ==========================================
# 3. CREATE BASE CLASS
# ==========================================
"""
Base class cho tất cả models

Tất cả models sẽ kế thừa từ Base:
- class User(Base): ...
- class Food(Base): ...

Base cung cấp:
- Table mapping
- Column definitions  
- Relationships
- Metadata
"""

Base = declarative_base()


# ==========================================
# 4. DEPENDENCY INJECTION for FastAPI
# ==========================================
"""
get_db() là dependency được inject vào FastAPI routes

Cách dùng trong route:
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

Luồng hoạt động:
1. Request đến → FastAPI gọi get_db()
2. get_db() tạo session mới
3. Session được inject vào route function
4. Route xử lý logic với session
5. Finally block đóng session (dù có lỗi hay không)
"""

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency
    
    Yields:
        Session: SQLAlchemy database session
        
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()  # Tạo session mới
    try:
        yield db  # Yield session cho route function
        # Route function xử lý ở đây...
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()  # Rollback nếu có lỗi
        raise  # Re-raise exception để FastAPI xử lý
    finally:
        db.close()  # Luôn đóng session (QUAN TRỌNG!)


# ==========================================
# 5. DATABASE UTILITIES
# ==========================================

def init_db():
    """
    Initialize database tables
    
    Tạo tất cả tables được định nghĩa trong models
    Chỉ dùng trong development, production dùng Alembic migrations
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


def drop_db():
    """
    Drop all database tables (NGUY HIỂM!)
    
    Chỉ dùng trong testing hoặc reset database
    """
    logger.warning("⚠️  Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped!")


def get_db_info():
    """
    Get database connection info (for debugging)
    
    Returns:
        dict: Database connection information
    """
    return {
        "url": str(engine.url).replace(engine.url.password or "", "***"),
        "pool_size": engine.pool.size(),
        "checked_in": engine.pool.checkedin(),
        "checked_out": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
        "echo": engine.echo,
    }


# ==========================================
# 6. CONTEXT MANAGER (Advanced)
# ==========================================
"""
Alternative way để dùng database session
Dùng trong background tasks hoặc scripts
"""

from contextlib import contextmanager

@contextmanager
def get_db_context():
    """
    Context manager for database sessions
    
    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
            print(user.email)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Auto commit khi không có lỗi
    except Exception:
        db.rollback()  # Auto rollback khi có lỗi
        raise
    finally:
        db.close()


# ==========================================
# TESTING - Run this file directly
# ==========================================

if __name__ == "__main__":
    """
    Test database connection
    
    Run: python -m app.database
    """
    print("=" * 60)
    print("🗄️  Testing Database Connection")
    print("=" * 60)
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL!")
            print(f"📊 Version: {version}")
            print()
            
        # Get pool info
        info = get_db_info()
        print("📊 Connection Pool Info:")
        print(f"   URL: {info['url']}")
        print(f"   Pool size: {info['pool_size']}")
        print(f"   Checked in: {info['checked_in']}")
        print(f"   Checked out: {info['checked_out']}")
        print(f"   Overflow: {info['overflow']}")
        print()
        
        # Test session creation
        print("🔄 Testing session creation...")
        db = SessionLocal()
        print(f"✅ Session created: {db}")
        db.close()
        print("✅ Session closed successfully!")
        
        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ DATABASE CONNECTION FAILED!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check if PostgreSQL is running:")
        print("   docker compose ps")
        print("2. Check DATABASE_URL in .env file")
        print("3. Check PostgreSQL logs:")
        print("   docker compose logs postgres")