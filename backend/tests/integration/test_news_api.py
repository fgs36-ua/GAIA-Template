# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
"""
API Integration Tests for News Endpoints

Tests the HTTP layer with TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.main import app
from app.core.database import get_db
from app.core.security import require_admin, CurrentUser
from app.infrastructure.db.base import Base


# Use the same database URL as conftest.py
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://postgres:postgres@db:5432/appdb"
)


@pytest.fixture(scope="module")
def test_engine():
    """Create test database engine."""
    return create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="module")
def test_tables(test_engine):
    """Ensure tables exist (may already exist from migrations)."""
    # Don't drop tables - migrations handle schema
    Base.metadata.create_all(test_engine, checkfirst=True)
    yield


@pytest.fixture
def test_db_session(test_engine, test_tables):
    """Create a test session with transaction rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(test_db_session):
    """Create a test user for API tests."""
    from app.infrastructure.models.user import User
    
    user = User(
        email="api-test@example.com",
        hashed_password="test_password_hash",
        full_name="API Test Admin",
        is_active=True,
        is_superuser=True,
    )
    test_db_session.add(user)
    test_db_session.flush()  # Get the user ID without committing
    
    return user


@pytest.fixture
def client(test_db_session, test_user):
    """Create test client with database and security overrides."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    def override_require_admin():
        return CurrentUser(
            id=test_user.id,
            email=test_user.email,
            is_active=True,
            is_superuser=True,
        )
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = override_require_admin
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


class TestCreateNewsAPI:
    """API tests for POST /api/news."""
    
    def test_create_news_returns_201(self, client):
        """Test that valid request returns 201 Created."""
        # Act
        response = client.post(
            "/api/news",
            json={
                "title": "API Test Article",
                "summary": "Test summary",
                "scope": "GENERAL",
            }
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "API Test Article"
        assert data["status"] == "DRAFT"
        assert "id" in data
    
    def test_create_news_xss_sanitized(self, client):
        """Test that XSS is sanitized in response."""
        # Act
        response = client.post(
            "/api/news",
            json={
                "title": "XSS Test",
                "content": "<p>Hello</p><script>alert('xss')</script>",
            }
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "<script>" not in data["content"]
        assert "<p>Hello</p>" in data["content"]
    
    def test_create_news_without_title_returns_422(self, client):
        """Test that missing title returns 422."""
        # Act
        response = client.post(
            "/api/news",
            json={
                "summary": "No title",
            }
        )
        
        # Assert
        assert response.status_code == 422
    
    def test_create_news_with_empty_title_returns_422(self, client):
        """Test that empty title returns 422."""
        # Act
        response = client.post(
            "/api/news",
            json={
                "title": "",
            }
        )
        
        # Assert
        assert response.status_code == 422
    
    def test_create_news_with_internal_scope(self, client):
        """Test creation with INTERNAL scope."""
        # Act
        response = client.post(
            "/api/news",
            json={
                "title": "Internal Article",
                "scope": "INTERNAL",
            }
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["scope"] == "INTERNAL"
    
    def test_create_news_rejects_extra_fields(self, client):
        """Test that extra fields are rejected (strict validation)."""
        # Act
        response = client.post(
            "/api/news",
            json={
                "title": "Test",
                "malicious_field": "should be rejected",
            }
        )
        
        # Assert
        assert response.status_code == 422
