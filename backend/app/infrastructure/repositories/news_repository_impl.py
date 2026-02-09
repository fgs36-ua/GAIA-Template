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
