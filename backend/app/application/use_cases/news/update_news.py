# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]
"""
Update News Use Case

Orchestrates updating an existing news article with:
- XSS sanitization for rich text content
- Preservation of published_at and status
- Not-found validation
"""

import logging
from uuid import UUID

import bleach

from app.domain.entities.news import News, NewsScope
from app.domain.repositories.news_repository import NewsRepository
from app.core.exceptions import NotFoundException


logger = logging.getLogger(__name__)

# Allowed HTML tags for rich text content (XSS prevention)
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'blockquote', 'pre', 'code'
]
ALLOWED_ATTRS = {'a': ['href', 'title']}


class UpdateNewsUseCase:
    """Use case for updating an existing news article.
    
    Enforces business rules:
    - Article must exist and not be deleted
    - Content is sanitized to prevent XSS attacks
    - published_at and status are preserved
    """
    
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def execute(
        self,
        id: UUID,
        title: str,
        summary: str | None = None,
        content: str | None = None,
        scope: NewsScope | None = None,
        cover_url: str | None = None,
    ) -> News:
        """Update an existing news article.
        
        Args:
            id: Article ID to update
            title: New article headline (required)
            summary: New brief description
            content: New rich text body (will be sanitized)
            scope: New visibility scope
            cover_url: New cover image URL
            
        Returns:
            The updated News entity
            
        Raises:
            NotFoundException: If article does not exist or is deleted
        """
        # Fetch existing article
        existing = self.repository.get_by_id(id)
        if not existing:
            raise NotFoundException(f"News article with id {id} not found")

        # Sanitize rich text content to prevent XSS
        sanitized_content = None
        if content:
            sanitized_content = bleach.clean(
                content,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRS,
                strip=True
            )

        # Update entity fields (preserve published_at and status)
        existing.title = title
        existing.summary = summary
        existing.content = sanitized_content
        if scope is not None:
            existing.scope = scope
        existing.cover_url = cover_url
        # Note: status and published_at are NOT modified

        updated_news = self.repository.update(existing)

        # Audit log
        logger.info(
            f"News article updated: id={id}, "
            f"title='{title[:50]}...'"
        )

        return updated_news
