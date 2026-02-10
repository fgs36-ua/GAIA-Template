# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
"""
News Repository Implementation (Adapter)

SQLAlchemy-based implementation of the NewsRepository interface.
Adapter pattern following hexagonal architecture.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.news import News
from app.domain.repositories.news_repository import NewsRepository
from app.infrastructure.db.mappers.news_mapper import NewsMapper


class NewsRepositoryImpl(NewsRepository):
    """SQLAlchemy implementation of NewsRepository.
    
    Handles all database operations for News aggregate.
    """
    
    def __init__(self, db: Session):
        self.db = db

    def create(self, news: News) -> News:
        """Persist a new news article and return it with generated ID."""
        from app.infrastructure.models.news import News as NewsModel
        
        model = NewsMapper.to_model(news)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return NewsMapper.to_entity(model)
    
    def get_by_id(self, news_id: UUID) -> Optional[News]:
        """Retrieve a news article by ID, or None if not found."""
        from app.infrastructure.models.news import News as NewsModel
        
        model = self.db.query(NewsModel).filter(
            NewsModel.id == news_id,
            NewsModel.is_deleted == False
        ).first()
        
        if model is None:
            return None
        
        return NewsMapper.to_entity(model)

    # [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]
    def update(self, news: News) -> News:
        """Update an existing news article and return updated entity."""
        from datetime import datetime, timezone
        from app.infrastructure.models.news import News as NewsModel
        
        model = self.db.query(NewsModel).filter(NewsModel.id == news.id).first()
        if not model:
            raise ValueError(f"News with id {news.id} not found")
        
        # Update mutable fields (preserve published_at, status, author_id)
        model.title = news.title
        model.summary = news.summary
        model.content = news.content
        model.scope = news.scope.value if hasattr(news.scope, 'value') else news.scope
        model.cover_url = news.cover_url
        model.updated_at = datetime.now(timezone.utc)
        # Note: published_at is NOT updated here (preserved)
        
        self.db.commit()
        self.db.refresh(model)
        return NewsMapper.to_entity(model)
