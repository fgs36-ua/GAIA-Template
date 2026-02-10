# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]
"""
Unit Tests for UpdateNewsUseCase

Tests the use case logic including XSS sanitization,
published_at preservation, and not-found handling.
Uses mocked repository for isolation.
"""

import pytest
from unittest.mock import Mock
from uuid import uuid4
from datetime import datetime

from app.application.use_cases.news.update_news import UpdateNewsUseCase
from app.domain.entities.news import News, NewsScope, NewsStatus
from app.core.exceptions import NotFoundException


class TestUpdateNewsUseCase:
    """Test suite for UpdateNewsUseCase."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = Mock()
        self.use_case = UpdateNewsUseCase(self.mock_repository)
        self.article_id = uuid4()
        self.author_id = uuid4()

    def _make_existing_article(self, **overrides) -> News:
        """Helper to create a test article entity."""
        defaults = dict(
            id=self.article_id,
            title="Original Title",
            author_id=self.author_id,
            summary="Original summary",
            content="<p>Original content</p>",
            status=NewsStatus.DRAFT,
            scope=NewsScope.GENERAL,
        )
        defaults.update(overrides)
        return News(**defaults)

    def test_update_successfully(self):
        """Test successful update with valid data."""
        # Arrange
        existing = self._make_existing_article()
        self.mock_repository.get_by_id.return_value = existing
        self.mock_repository.update.side_effect = lambda news: news

        # Act
        result = self.use_case.execute(
            id=self.article_id,
            title="New Title",
            summary="New summary",
        )

        # Assert
        assert result.title == "New Title"
        assert result.summary == "New summary"
        self.mock_repository.get_by_id.assert_called_once_with(self.article_id)
        self.mock_repository.update.assert_called_once()

    def test_preserves_published_at_for_published_articles(self):
        """Test that published_at is not changed when updating a published article."""
        # Arrange
        published_at = datetime(2026, 1, 15, 12, 0, 0)
        existing = self._make_existing_article(
            status=NewsStatus.PUBLISHED,
            published_at=published_at,
        )
        self.mock_repository.get_by_id.return_value = existing
        self.mock_repository.update.side_effect = lambda news: news

        # Act
        result = self.use_case.execute(
            id=self.article_id,
            title="Updated Published Title",
        )

        # Assert
        updated_entity = self.mock_repository.update.call_args[0][0]
        assert updated_entity.published_at == published_at  # Unchanged
        assert updated_entity.status == NewsStatus.PUBLISHED  # Status preserved

    def test_preserves_status(self):
        """Test that article status is never changed by update."""
        # Arrange
        existing = self._make_existing_article(status=NewsStatus.ARCHIVED)
        self.mock_repository.get_by_id.return_value = existing
        self.mock_repository.update.side_effect = lambda news: news

        # Act
        self.use_case.execute(id=self.article_id, title="New Title")

        # Assert
        updated_entity = self.mock_repository.update.call_args[0][0]
        assert updated_entity.status == NewsStatus.ARCHIVED

    def test_xss_sanitization_removes_script_tags(self):
        """Test that script tags are removed from content."""
        # Arrange
        existing = self._make_existing_article()
        self.mock_repository.get_by_id.return_value = existing
        self.mock_repository.update.side_effect = lambda news: news

        # Act
        self.use_case.execute(
            id=self.article_id,
            title="Test",
            content="<p>Hello</p><script>alert('xss')</script>",
        )

        # Assert
        updated_entity = self.mock_repository.update.call_args[0][0]
        assert "<script>" not in updated_entity.content
        assert "<p>Hello</p>" in updated_entity.content

    def test_raises_not_found_for_missing_article(self):
        """Test that NotFoundException is raised when article does not exist."""
        # Arrange
        self.mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException, match="not found"):
            self.use_case.execute(
                id=uuid4(),
                title="Does Not Matter",
            )

        self.mock_repository.update.assert_not_called()

    def test_none_content_remains_none(self):
        """Test that None content is not sanitized."""
        # Arrange
        existing = self._make_existing_article()
        self.mock_repository.get_by_id.return_value = existing
        self.mock_repository.update.side_effect = lambda news: news

        # Act
        result = self.use_case.execute(
            id=self.article_id,
            title="Updated",
            content=None,
        )

        # Assert
        assert result.content is None

    def test_updates_scope(self):
        """Test that scope is updated when provided."""
        # Arrange
        existing = self._make_existing_article(scope=NewsScope.GENERAL)
        self.mock_repository.get_by_id.return_value = existing
        self.mock_repository.update.side_effect = lambda news: news

        # Act
        self.use_case.execute(
            id=self.article_id,
            title="Test",
            scope=NewsScope.INTERNAL,
        )

        # Assert
        updated_entity = self.mock_repository.update.call_args[0][0]
        assert updated_entity.scope == NewsScope.INTERNAL

    def test_scope_unchanged_when_none(self):
        """Test that scope is preserved when not explicitly provided."""
        # Arrange
        existing = self._make_existing_article(scope=NewsScope.INTERNAL)
        self.mock_repository.get_by_id.return_value = existing
        self.mock_repository.update.side_effect = lambda news: news

        # Act
        self.use_case.execute(
            id=self.article_id,
            title="Test",
            scope=None,
        )

        # Assert
        updated_entity = self.mock_repository.update.call_args[0][0]
        assert updated_entity.scope == NewsScope.INTERNAL
