# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
"""
Create News Use Case

Orchestrates the creation of a news article with:
- XSS sanitization for rich text content
- Default status as DRAFT
- Audit logging capability
"""

import logging
from uuid import UUID

import bleach

from app.domain.entities.news import News, NewsScope, NewsStatus
from app.domain.repositories.news_repository import NewsRepository


logger = logging.getLogger(__name__)

# Allowed HTML tags for rich text content (XSS prevention)
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 
    'h1', 'h2', 'h3', 'h4', 'blockquote', 'pre', 'code'
]
ALLOWED_ATTRS = {'a': ['href', 'title']}


class CreateNewsUseCase:
    """Use case for creating a news article.
    
    Enforces business rules:
    - Articles are always created as DRAFT
    - Content is sanitized to prevent XSS attacks
    - Author is tracked for audit trail
    """
    
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def execute(
        self,
        title: str,
        author_id: UUID,
        summary: str | None = None,
        content: str | None = None,
        scope: NewsScope = NewsScope.GENERAL,
        cover_url: str | None = None,
    ) -> News:
        """Create a new news article as draft.
        
        Args:
            title: Article headline (required)
            author_id: ID of the admin creating the article
            summary: Brief description for lists
            content: Rich text body (will be sanitized)
            scope: Visibility scope (GENERAL or INTERNAL)
            cover_url: Optional cover image URL
            
        Returns:
            The created News entity with generated ID
        """
        # Sanitize rich text content to prevent XSS
        sanitized_content = None
        if content:
            sanitized_content = bleach.clean(
                content,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRS,
                strip=True
            )

        news = News(
            title=title,
            author_id=author_id,
            summary=summary,
            content=sanitized_content,
            scope=scope,
            cover_url=cover_url,
            status=NewsStatus.DRAFT,
        )

        created_news = self.repository.create(news)
        
        # Audit log
        logger.info(
            f"News article created: id={created_news.id}, "
            f"title='{title[:50]}...', author_id={author_id}, "
            f"scope={scope.value}"
        )

        return created_news
