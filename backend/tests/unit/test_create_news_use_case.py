# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
"""
Unit Tests for CreateNewsUseCase

Tests the use case logic including XSS sanitization.
Uses mocked repository for isolation.
"""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from app.application.use_cases.news.create_news import CreateNewsUseCase, ALLOWED_TAGS
from app.domain.entities.news import News, NewsScope, NewsStatus


class TestCreateNewsUseCase:
    """Test suite for CreateNewsUseCase."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = Mock()
        self.use_case = CreateNewsUseCase(self.mock_repository)
        self.author_id = uuid4()
    
    def test_create_news_with_valid_data(self):
        """Test successful creation with valid data."""
        # Arrange
        created_news = News(
            title="Test Article",
            author_id=self.author_id,
            status=NewsStatus.DRAFT,
        )
        self.mock_repository.create.return_value = created_news
        
        # Act
        result = self.use_case.execute(
            title="Test Article",
            author_id=self.author_id,
        )
        
        # Assert
        self.mock_repository.create.assert_called_once()
        assert result.title == "Test Article"
        assert result.status == NewsStatus.DRAFT
    
    def test_create_news_always_draft(self):
        """Test that articles are always created as DRAFT."""
        # Arrange
        def capture_news(news):
            return news
        
        self.mock_repository.create.side_effect = capture_news
        
        # Act
        result = self.use_case.execute(
            title="Test",
            author_id=self.author_id,
        )
        
        # Assert
        assert result.status == NewsStatus.DRAFT
    
    def test_xss_sanitization_removes_script_tags(self):
        """Test that script tags are removed from content."""
        # Arrange
        malicious_content = "<p>Hello</p><script>alert('xss')</script>"
        
        def capture_news(news):
            return news
        
        self.mock_repository.create.side_effect = capture_news
        
        # Act
        result = self.use_case.execute(
            title="Test",
            author_id=self.author_id,
            content=malicious_content,
        )
        
        # Assert - bleach removes script tags (text may remain but is harmless)
        assert "<script>" not in result.content
        assert "</script>" not in result.content
        assert "<p>Hello</p>" in result.content
    
    def test_xss_sanitization_removes_event_handlers(self):
        """Test that event handlers are removed from content."""
        # Arrange
        malicious_content = '<p onclick="alert(1)">Click me</p>'
        
        def capture_news(news):
            return news
        
        self.mock_repository.create.side_effect = capture_news
        
        # Act
        result = self.use_case.execute(
            title="Test",
            author_id=self.author_id,
            content=malicious_content,
        )
        
        # Assert
        assert 'onclick' not in result.content
        assert '<p>' in result.content
    
    def test_sanitization_preserves_allowed_tags(self):
        """Test that allowed HTML tags are preserved."""
        # Arrange
        valid_content = "<p>Hello <strong>World</strong></p><a href='http://example.com'>Link</a>"
        
        def capture_news(news):
            return news
        
        self.mock_repository.create.side_effect = capture_news
        
        # Act
        result = self.use_case.execute(
            title="Test",
            author_id=self.author_id,
            content=valid_content,
        )
        
        # Assert
        assert "<p>" in result.content
        assert "<strong>" in result.content
        assert "<a " in result.content
    
    def test_create_with_scope_internal(self):
        """Test creation with INTERNAL scope."""
        # Arrange
        def capture_news(news):
            return news
        
        self.mock_repository.create.side_effect = capture_news
        
        # Act
        result = self.use_case.execute(
            title="Internal News",
            author_id=self.author_id,
            scope=NewsScope.INTERNAL,
        )
        
        # Assert
        assert result.scope == NewsScope.INTERNAL
    
    def test_create_with_all_optional_fields(self):
        """Test creation with all optional fields populated."""
        # Arrange
        def capture_news(news):
            return news
        
        self.mock_repository.create.side_effect = capture_news
        
        # Act
        result = self.use_case.execute(
            title="Full Article",
            author_id=self.author_id,
            summary="This is a summary",
            content="<p>Content here</p>",
            scope=NewsScope.GENERAL,
            cover_url="https://example.com/image.jpg",
        )
        
        # Assert
        assert result.title == "Full Article"
        assert result.summary == "This is a summary"
        assert result.cover_url == "https://example.com/image.jpg"
    
    def test_none_content_is_not_sanitized(self):
        """Test that None content remains None."""
        # Arrange
        def capture_news(news):
            return news
        
        self.mock_repository.create.side_effect = capture_news
        
        # Act
        result = self.use_case.execute(
            title="No Content",
            author_id=self.author_id,
            content=None,
        )
        
        # Assert
        assert result.content is None
