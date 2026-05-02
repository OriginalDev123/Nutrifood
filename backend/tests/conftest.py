"""
Pytest Configuration - Shared Fixtures
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
import uuid
import os

from app.database import Base
from app.main import app
from app.database import get_db


# === DATABASE TEST FIXTURES ===

@pytest.fixture(scope="function")
def db_session():
    """
    Create a test database session using PostgreSQL test database
    Each test gets a fresh transaction that rolls back
    """
    # Use environment variable or default test database
    DATABASE_URL = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://nutriai_user:nutriai_password@localhost:5432/nutriai_db"
    )
    
    # Create engine
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )
    
    # Create all tables (idempotent)
    Base.metadata.create_all(bind=engine)
    
    # Create connection
    connection = engine.connect()
    
    # Begin a non-ORM transaction
    transaction = connection.begin()
    
    # Create session bound to the connection
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()
    
    # Begin a nested transaction (using SAVEPOINT)
    session.begin_nested()
    
    # Each time session is committed, re-open the nested transaction
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()
    
    try:
        yield session
    finally:
        session.close()
        # Rollback the outer transaction to clean up all changes
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with overridden database dependency
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up override
    app.dependency_overrides.clear()


# === USER TEST FIXTURES ===

@pytest.fixture
def test_user(db_session):
    """
    Create a test user in the database
    """
    from app.models.user import User
    from app.utils.security import get_password_hash
    
    user = User(
        user_id=uuid.uuid4(),
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        is_active=True,
        is_admin=False
    )
    
    db_session.add(user)
    db_session.commit()  # Commit within nested transaction
    
    return user


@pytest.fixture
def test_superuser(db_session):
    """
    Create a test superuser in the database
    """
    from app.models.user import User
    from app.utils.security import get_password_hash
    
    user = User(
        user_id=uuid.uuid4(),
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword123"),
        is_active=True,
        is_admin=True
    )
    
    db_session.add(user)
    db_session.flush()  # Flush to get ID without committing
    
    return user
