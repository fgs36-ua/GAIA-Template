# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
"""
Integration Tests for News Repository

Tests repository with real database connection.
"""

import pytest
from uuid import uuid4

from app.infrastructure.repositories.news_repository_impl import NewsRepositoryImpl
from app.domain.entities.news import News, NewsStatus, NewsScope


class TestNewsRepositoryImpl:
    """Integration tests for NewsRepositoryImpl."""
    
    def test_create_news_persists_to_database(self, db_session, sample_user):
        """Test that create() persists news to database and returns entity."""
        # Arrange
        repository = NewsRepositoryImpl(db_session)
        news = News(
            title="Integration Test Article",
            author_id=sample_user.id,
            summary="Test summary",
            content="<p>Test content</p>",
            scope=NewsScope.GENERAL,
        )
        
        # Act
        created = repository.create(news)
        
        # Assert
        assert created.id is not None
        assert created.title == "Integration Test Article"
        assert created.status == NewsStatus.DRAFT
        assert created.author_id == sample_user.id
    
    def test_create_news_generates_timestamps(self, db_session, sample_user):
        """Test that timestamps are generated on create."""
        # Arrange
        repository = NewsRepositoryImpl(db_session)
        news = News(
            title="Timestamp Test",
            author_id=sample_user.id,
        )
        
        # Act
        created = repository.create(news)
        
        # Assert
        assert created.created_at is not None
    
    def test_get_by_id_returns_news(self, db_session, sample_user):
        """Test that get_by_id returns existing news."""
        # Arrange
        repository = NewsRepositoryImpl(db_session)
        news = News(
            title="Fetch Test",
            author_id=sample_user.id,
        )
        created = repository.create(news)
        
        # Act
        fetched = repository.get_by_id(created.id)
        
        # Assert
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.title == "Fetch Test"
    
    def test_get_by_id_returns_none_for_missing(self, db_session):
        """Test that get_by_id returns None for non-existent ID."""
        # Arrange
        repository = NewsRepositoryImpl(db_session)
        
        # Act
        result = repository.get_by_id(uuid4())
        
        # Assert
        assert result is None
    
    def test_get_by_id_excludes_soft_deleted(self, db_session, sample_user):
        """Test that get_by_id excludes soft-deleted news."""
        # Arrange
        from app.infrastructure.models.news import News as NewsModel
        
        repository = NewsRepositoryImpl(db_session)
        news = News(
            title="Deleted Test",
            author_id=sample_user.id,
        )
        created = repository.create(news)
        
        # Soft delete via model
        model = db_session.query(NewsModel).filter_by(id=created.id).first()
        model.is_deleted = True
        db_session.commit()
        
        # Act
        result = repository.get_by_id(created.id)
        
        # Assert
        assert result is None
