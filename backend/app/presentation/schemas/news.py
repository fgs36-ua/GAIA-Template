# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
"""
News API Schemas

Pydantic V2 request/response DTOs for the News API.
Supports validation, serialization, and OpenAPI documentation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.domain.entities.news import NewsScope, NewsStatus


class CreateNewsRequest(BaseModel):
    """Request schema for creating a news article."""
    
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        description="Article headline"
    )
    summary: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Brief description for lists"
    )
    content: Optional[str] = Field(
        None, 
        description="Rich text content (HTML) - will be sanitized"
    )
    scope: NewsScope = Field(
        NewsScope.GENERAL, 
        description="Visibility scope (GENERAL or INTERNAL)"
    )
    cover_url: Optional[str] = Field(
        None, 
        max_length=2048, 
        description="Cover image URL"
    )

    model_config = ConfigDict(extra="forbid")


# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]
class UpdateNewsRequest(BaseModel):
    """Request schema for updating an existing news article."""
    
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        description="Article headline"
    )
    summary: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Brief description for lists"
    )
    content: Optional[str] = Field(
        None, 
        description="Rich text content (HTML) - will be sanitized"
    )
    scope: Optional[NewsScope] = Field(
        None, 
        description="Visibility scope (GENERAL or INTERNAL)"
    )
    cover_url: Optional[str] = Field(
        None, 
        max_length=2048, 
        description="Cover image URL"
    )

    model_config = ConfigDict(extra="forbid")


class NewsResponse(BaseModel):
    """Response schema for a news article."""
    
    id: UUID
    title: str
    summary: Optional[str]
    content: Optional[str]
    status: NewsStatus
    scope: NewsScope
    author_id: UUID
    cover_url: Optional[str]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
