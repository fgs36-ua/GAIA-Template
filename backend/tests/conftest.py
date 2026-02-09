# [Feature: Infrastructure] [Story: Backend Setup] [Ticket: NM-ADMIN-001-DB-T01]
"""
Pytest Configuration and Fixtures

Provides database session and common fixtures for testing.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.infrastructure.db.base import Base


# Test database URL - inside Docker, use db:5432 (internal network)
# Falls back to localhost:5455 for local development outside Docker
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://postgres:postgres@db:5432/appdb"
)


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    return create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables for testing."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
    """Provide a transactional database session for tests."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing author relationships."""
    from app.infrastructure.models.user import User
    
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_placeholder",
        full_name="Test User",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user

