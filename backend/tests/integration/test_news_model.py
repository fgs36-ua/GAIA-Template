# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-DB-T01]
"""
News Model Integration Tests

Tests for the News SQLAlchemy model and database operations.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.infrastructure.models.news import News, NewsStatus, NewsScope
from app.infrastructure.models.user import User


class TestNewsStatusEnum:
    """Test NewsStatus enum values."""
    
    def test_draft_value(self):
        assert NewsStatus.DRAFT.value == "DRAFT"
    
    def test_published_value(self):
        assert NewsStatus.PUBLISHED.value == "PUBLISHED"
    
    def test_archived_value(self):
        assert NewsStatus.ARCHIVED.value == "ARCHIVED"
    
    def test_enum_is_string_subclass(self):
        """Enum values should be string for JSON serialization."""
        assert isinstance(NewsStatus.DRAFT, str)


class TestNewsScopeEnum:
    """Test NewsScope enum values."""
    
    def test_general_value(self):
        assert NewsScope.GENERAL.value == "GENERAL"
    
    def test_internal_value(self):
        assert NewsScope.INTERNAL.value == "INTERNAL"
    
    def test_enum_is_string_subclass(self):
        assert isinstance(NewsScope.GENERAL, str)


class TestNewsModel:
    """Test News model instantiation and defaults."""
    
    def test_create_news_with_minimal_data(self, db_session, sample_user):
        """Test creating news with only required fields."""
        news = News(
            title="Test Article",
            author_id=sample_user.id
        )
        db_session.add(news)
        db_session.commit()
        db_session.refresh(news)
        
        assert news.id is not None
        assert news.title == "Test Article"
        assert news.status == NewsStatus.DRAFT
        assert news.scope == NewsScope.GENERAL
        assert news.is_deleted is False
        assert news.summary is None
        assert news.content is None
        assert news.published_at is None
    
    def test_create_news_with_all_fields(self, db_session, sample_user):
        """Test creating news with all fields populated."""
        now = datetime.now(timezone.utc)
        news = News(
            title="Full Article",
            summary="This is a summary",
            content="<p>Rich HTML content</p>",
            status=NewsStatus.PUBLISHED,
            scope=NewsScope.INTERNAL,
            author_id=sample_user.id,
            cover_url="https://example.com/image.jpg",
            published_at=now,
        )
        db_session.add(news)
        db_session.commit()
        db_session.refresh(news)
        
        assert news.title == "Full Article"
        assert news.summary == "This is a summary"
        assert news.content == "<p>Rich HTML content</p>"
        assert news.status == NewsStatus.PUBLISHED
        assert news.scope == NewsScope.INTERNAL
        assert news.cover_url == "https://example.com/image.jpg"
        assert news.published_at == now
    
    def test_news_author_relationship(self, db_session, sample_user):
        """Test that news has correct relationship to author."""
        news = News(
            title="Author Test",
            author_id=sample_user.id
        )
        db_session.add(news)
        db_session.commit()
        db_session.refresh(news)
        
        assert news.author.id == sample_user.id
        assert news.author.email == sample_user.email
    
    def test_soft_delete_flag(self, db_session, sample_user):
        """Test soft delete functionality."""
        news = News(
            title="To Be Deleted",
            author_id=sample_user.id
        )
        db_session.add(news)
        db_session.commit()
        
        # Soft delete
        news.is_deleted = True
        db_session.commit()
        db_session.refresh(news)
        
        assert news.is_deleted is True
        # Record still exists
        assert db_session.query(News).filter_by(id=news.id).first() is not None
    
    def test_timestamps_auto_set(self, db_session, sample_user):
        """Test that created_at and updated_at are auto-set."""
        news = News(
            title="Timestamp Test",
            author_id=sample_user.id
        )
        db_session.add(news)
        db_session.commit()
        db_session.refresh(news)
        
        assert news.created_at is not None
        # Note: updated_at behavior depends on DB default vs Python default


# Fixtures
@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        id=uuid4(),
        email=f"test-{uuid4()}@example.com",
        hashed_password="hashedpassword123",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
