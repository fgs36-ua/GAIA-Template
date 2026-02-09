# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
"""
News Mapper

Converts between domain entity and SQLAlchemy model.
Keeps domain and infrastructure layers decoupled.
"""

from app.domain.entities.news import News as NewsEntity, NewsStatus as DomainStatus, NewsScope as DomainScope
from app.infrastructure.models.news import News as NewsModel, NewsStatus as ModelStatus, NewsScope as ModelScope


class NewsMapper:
    """Bidirectional mapper between News domain entity and SQLAlchemy model."""
    
    @staticmethod
    def to_model(entity: NewsEntity) -> NewsModel:
        """Convert domain entity to SQLAlchemy model."""
        return NewsModel(
            id=entity.id,
            title=entity.title,
            summary=entity.summary,
            content=entity.content,
            status=ModelStatus(entity.status.value),
            scope=ModelScope(entity.scope.value),
            author_id=entity.author_id,
            cover_url=entity.cover_url,
            published_at=entity.published_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_deleted=entity.is_deleted,
        )

    @staticmethod
    def to_entity(model: NewsModel) -> NewsEntity:
        """Convert SQLAlchemy model to domain entity."""
        return NewsEntity(
            id=model.id,
            title=model.title,
            summary=model.summary,
            content=model.content,
            status=DomainStatus(model.status.value),
            scope=DomainScope(model.scope.value),
            author_id=model.author_id,
            cover_url=model.cover_url,
            published_at=model.published_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=model.is_deleted,
        )
