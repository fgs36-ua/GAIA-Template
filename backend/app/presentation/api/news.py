# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]
"""
News API Router

Exposes HTTP endpoints for news article management.
Admin-only access enforced via security dependencies.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.core.security import require_admin, CurrentUser
from app.application.use_cases.news.create_news import CreateNewsUseCase
from app.application.use_cases.news.update_news import UpdateNewsUseCase
from app.infrastructure.repositories.news_repository_impl import NewsRepositoryImpl
from app.presentation.schemas.news import CreateNewsRequest, UpdateNewsRequest, NewsResponse

router = APIRouter(prefix="/news", tags=["news"])


@router.post(
    "", 
    response_model=NewsResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a news article",
    description="Create a new news article as draft. Admin only."
)
def create_news(
    request: CreateNewsRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
) -> NewsResponse:
    """Create a new news article as draft.
    
    - Requires admin authentication
    - Content is sanitized to prevent XSS
    - Article is created with DRAFT status
    """
    repository = NewsRepositoryImpl(db)
    use_case = CreateNewsUseCase(repository)
    
    news = use_case.execute(
        title=request.title,
        author_id=current_user.id,
        summary=request.summary,
        content=request.content,
        scope=request.scope,
        cover_url=request.cover_url,
    )
    
    return NewsResponse(
        id=news.id,
        title=news.title,
        summary=news.summary,
        content=news.content,
        status=news.status,
        scope=news.scope,
        author_id=news.author_id,
        cover_url=news.cover_url,
        published_at=news.published_at,
        created_at=news.created_at,
        updated_at=news.updated_at,
    )


# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]
@router.put(
    "/{news_id}",
    response_model=NewsResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a news article",
    description="Update an existing news article. Admin only."
)
def update_news(
    news_id: UUID,
    request: UpdateNewsRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
) -> NewsResponse:
    """Update an existing news article.
    
    - Requires admin authentication
    - Content is sanitized to prevent XSS
    - Preserves published_at and status
    """
    repository = NewsRepositoryImpl(db)
    use_case = UpdateNewsUseCase(repository)
    
    try:
        news = use_case.execute(
            id=news_id,
            title=request.title,
            summary=request.summary,
            content=request.content,
            scope=request.scope,
            cover_url=request.cover_url,
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )
    
    return NewsResponse(
        id=news.id,
        title=news.title,
        summary=news.summary,
        content=news.content,
        status=news.status,
        scope=news.scope,
        author_id=news.author_id,
        cover_url=news.cover_url,
        published_at=news.published_at,
        created_at=news.created_at,
        updated_at=news.updated_at,
    )
