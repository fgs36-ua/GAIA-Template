# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
"""
News Repository Interface (Port)

Abstract contract for news persistence operations.
Follows hexagonal architecture with repository pattern.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.news import News


class NewsRepository(ABC):
    """Abstract repository for News aggregate.
    
    Defines the contract that infrastructure adapters must implement.
    """
    
    @abstractmethod
    def create(self, news: News) -> News:
        """Persist a new news article and return it with generated ID."""
        pass
    
    @abstractmethod
    def get_by_id(self, news_id: UUID) -> Optional[News]:
        """Retrieve a news article by ID, or None if not found."""
        pass

    # [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]
    @abstractmethod
    def update(self, news: News) -> News:
        """Update an existing news article and return updated entity."""
        pass
