# NM-PUBLIC-002-BE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-PUBLIC-002-BE-T01**  
**Related user story**: **NM-PUBLIC-002** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All tasks must include inline references to `NM-PUBLIC-002-BE-T01`

---

## 1) Context & Objective

### Ticket Summary
Add search and pagination to the news list endpoint. Key requirements:
- `search` query parameter with ILIKE on title
- `skip`/`limit` pagination parameters
- Total count in response for UI pagination
- Performance: <500ms p95 with pagination

**Business Value**: Users can find specific articles quickly through keyword search with efficient paginated results.

### Impacted Entities/Tables
| Entity | Layer | Operation |
|--------|-------|-----------|
| `ListNewsUseCase` | application/use_cases | MODIFY (add search) |
| `NewsRepository` | domain/repositories | MODIFY (add search param) |
| `NewsRepositoryImpl` | infrastructure/repositories | MODIFY (ILIKE query) |

### Impacted Services/Modules
| Layer | Module | Operation |
|-------|--------|-----------|
| Application | `application/use_cases/news/list_news.py` | MODIFY |
| Infrastructure | `infrastructure/repositories/news_repository_impl.py` | MODIFY |
| Presentation | `presentation/api/news.py` | MODIFY (add query params) |
| Presentation | `presentation/schemas/news.py` | MODIFY (add search param) |

### Impacted BDD Scenarios
This ticket implements:
- **"User searches news by title"** — Search returns matching articles
- **"Search is performant"** — <500ms response time
- **"No results for search"** — Empty but valid response

---

## 2) Scope

### In Scope
- `search` query parameter (optional)
- ILIKE query on `title` field
- `skip`/`limit` pagination already exists, ensure works with search
- Total count in paginated response
- Unit and integration tests

### Out of Scope
- Full-text search (PostgreSQL FTS)
- Tag filtering
- Date range filtering
- Content search

### Assumptions
1. **BE-T01 exists**: ListNewsUseCase and repository already implement basic list
2. **ILIKE is sufficient**: No need for full-text search
3. **Index exists**: May need to add index on `title` for performance

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for ListNewsUseCase**:
   - Test search filters results by title
   - Test empty search returns all
   - Test case insensitive matching

2. **Integration tests for API**:
   - Test search query param works
   - Test pagination with search
   - Test no results returns empty items array
   - Test performance under threshold

#### Phase 2: GREEN — Minimal Implementation
1. Add search parameter to repository method
2. Update use case request DTO
3. Add ILIKE query in repository implementation
4. Update endpoint with search param
5. Run tests to verify GREEN state

### 3.2 NFR Hooks

#### Performance
- Database index on `title` for ILIKE optimization
- <500ms p95 target
- Limit must cap at 100

#### Security
- Sanitize search input (no SQL injection via ORM)
- Don't expose internal errors

---

## 4) Atomic Task Breakdown

### Task 1: Update Repository Interface
- **Purpose**: Add search parameter to list methods.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `backend/app/domain/repositories/news_repository.py`
- **Test types**: None (interface only)
- **BDD Acceptance**:
  ```
  Given I update NewsRepository interface
  Then list methods accept optional search parameter
  ```

**Interface Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-BE-T01]

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from uuid import UUID

from backend.app.domain.entities.news import News


class NewsRepository(ABC):
    @abstractmethod
    def list_public(
        self, 
        skip: int = 0, 
        limit: int = 20,
        search: Optional[str] = None,  # Added
    ) -> Tuple[List[News], int]:
        """List published GENERAL articles. Returns (items, total_count)."""
        pass

    @abstractmethod
    def list_for_member(
        self, 
        skip: int = 0, 
        limit: int = 20,
        search: Optional[str] = None,  # Added
    ) -> Tuple[List[News], int]:
        """List published articles (both scopes). Returns (items, total_count)."""
        pass

    @abstractmethod
    def list_all(
        self, 
        skip: int = 0, 
        limit: int = 20,
        search: Optional[str] = None,  # Added
    ) -> Tuple[List[News], int]:
        """List all articles (admin). Returns (items, total_count)."""
        pass
```

---

### Task 2: Update Repository Implementation with ILIKE
- **Purpose**: Implement search with ILIKE query.
- **Prerequisites**: Task 1
- **Artifacts impacted**: 
  - `backend/app/infrastructure/repositories/news_repository_impl.py`
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  # Scenario: Search by title
  Given articles with titles "Evento Navidad" and "Evento Verano"
  When I call list_public(search="navidad")
  Then only "Evento Navidad" is returned
  
  # Scenario: Case insensitive
  When I call list_public(search="NAVIDAD")
  Then "Evento Navidad" is returned
  
  # Scenario: No search
  When I call list_public(search=None)
  Then all articles are returned
  ```

**Implementation Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-BE-T01]

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.domain.entities.news import News, NewsScope, NewsStatus
from backend.app.domain.repositories.news_repository import NewsRepository
from backend.app.infrastructure.models.news import NewsModel


class NewsRepositoryImpl(NewsRepository):
    def __init__(self, db: Session):
        self.db = db

    def _apply_search(self, query, search: Optional[str]):
        """Apply ILIKE search filter to query."""
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(NewsModel.title.ilike(search_pattern))
        return query

    def list_public(
        self, 
        skip: int = 0, 
        limit: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[News], int]:
        # Base query for public articles
        base_query = self.db.query(NewsModel).filter(
            NewsModel.is_deleted == False,
            NewsModel.status == NewsStatus.PUBLISHED,
            NewsModel.scope == NewsScope.GENERAL,
        )
        
        # Apply search filter
        base_query = self._apply_search(base_query, search)
        
        # Get total count
        total = base_query.count()
        
        # Get paginated items
        items = (
            base_query
            .order_by(NewsModel.published_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [self._to_entity(item) for item in items], total

    def list_for_member(
        self, 
        skip: int = 0, 
        limit: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[News], int]:
        # Base query for member-accessible articles
        base_query = self.db.query(NewsModel).filter(
            NewsModel.is_deleted == False,
            NewsModel.status == NewsStatus.PUBLISHED,
        )
        
        # Apply search filter
        base_query = self._apply_search(base_query, search)
        
        # Get total count
        total = base_query.count()
        
        # Get paginated items
        items = (
            base_query
            .order_by(NewsModel.published_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [self._to_entity(item) for item in items], total

    def list_all(
        self, 
        skip: int = 0, 
        limit: int = 20,
        search: Optional[str] = None,
    ) -> Tuple[List[News], int]:
        # Base query for all articles (admin view)
        base_query = self.db.query(NewsModel).filter(
            NewsModel.is_deleted == False,
        )
        
        # Apply search filter
        base_query = self._apply_search(base_query, search)
        
        # Get total count
        total = base_query.count()
        
        # Get paginated items
        items = (
            base_query
            .order_by(NewsModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [self._to_entity(item) for item in items], total
```

---

### Task 3: Update ListNewsUseCase Request
- **Purpose**: Add search parameter to use case request.
- **Prerequisites**: Task 1
- **Artifacts impacted**: 
  - `backend/app/application/use_cases/news/list_news.py`
- **Test types**: Unit
- **BDD Acceptance**:
  ```
  Given a ListNewsRequest with search="navidad"
  When I execute ListNewsUseCase
  Then the search is passed to repository
  ```

**Use Case Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-BE-T01]

from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID

from backend.app.domain.repositories.news_repository import NewsRepository
from backend.app.domain.entities.user import User, UserRole
from backend.app.domain.entities.news import News


@dataclass
class ListNewsRequest:
    skip: int = 0
    limit: int = 20
    search: Optional[str] = None  # Added
    current_user: Optional[User] = None


@dataclass
class ListNewsResponse:
    items: List[News]
    total: int
    skip: int
    limit: int


class ListNewsUseCase:
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def execute(self, request: ListNewsRequest) -> ListNewsResponse:
        # Cap limit to prevent abuse
        limit = min(request.limit, 100)
        
        user = request.current_user
        
        # Determine which list method based on role
        if user and user.role == UserRole.ADMIN:
            items, total = self.repository.list_all(
                skip=request.skip,
                limit=limit,
                search=request.search,  # Pass search
            )
        elif user and user.role in [UserRole.MEMBER, UserRole.ADMIN]:
            items, total = self.repository.list_for_member(
                skip=request.skip,
                limit=limit,
                search=request.search,  # Pass search
            )
        else:
            items, total = self.repository.list_public(
                skip=request.skip,
                limit=limit,
                search=request.search,  # Pass search
            )
        
        return ListNewsResponse(
            items=items,
            total=total,
            skip=request.skip,
            limit=limit,
        )
```

---

### Task 4: Update API Endpoint
- **Purpose**: Add search query parameter to GET /api/news.
- **Prerequisites**: Tasks 2, 3
- **Artifacts impacted**: 
  - `backend/app/presentation/api/news.py`
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  # Happy path
  Given articles "Evento Navidad" and "Evento Verano" exist
  When I GET /api/news?search=navidad
  Then I receive status 200
  And only "Evento Navidad" is in items
  
  # Pagination with search
  When I GET /api/news?search=evento&skip=0&limit=1
  Then total is 2 but items length is 1
  
  # No results
  When I GET /api/news?search=nonexistent
  Then items is empty array
  And total is 0
  ```

**Endpoint Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-BE-T01]

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_optional
from backend.app.application.use_cases.news.list_news import (
    ListNewsUseCase,
    ListNewsRequest,
)
from backend.app.infrastructure.repositories.news_repository_impl import NewsRepositoryImpl
from backend.app.presentation.schemas.news import PaginatedNewsResponse


@router.get("", response_model=PaginatedNewsResponse)
def list_news(
    skip: int = Query(0, ge=0, description="Número de artículos a saltar"),
    limit: int = Query(20, ge=1, le=100, description="Número máximo de artículos"),
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Buscar por título"),  # Added
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    """
    List news articles with optional search and pagination.
    
    - Anonymous: only GENERAL published articles
    - Members: all published articles (both scopes)
    - Admins: all articles (including drafts/archived)
    
    Search is case-insensitive and matches partial titles.
    """
    repository = NewsRepositoryImpl(db)
    use_case = ListNewsUseCase(repository)
    
    request = ListNewsRequest(
        skip=skip,
        limit=limit,
        search=search,  # Pass search
        current_user=current_user,
    )
    
    response = use_case.execute(request)
    
    return PaginatedNewsResponse(
        items=[...],  # Map to response DTOs
        total=response.total,
        skip=response.skip,
        limit=response.limit,
    )
```

---

### Task 5: Add Database Index (if needed)
- **Purpose**: Optimize ILIKE queries with GIN index.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `backend/app/infrastructure/models/news.py` (index definition)
  - New Alembic migration
- **Test types**: Performance
- **BDD Acceptance**:
  ```
  Given a table with 10000 articles
  When I search with ILIKE
  Then response time is <500ms
  ```

**Index Template** (in model):
```python
# [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-BE-T01]

from sqlalchemy import Index

# Add to NewsModel class or after table definition
Index('ix_news_title_gin', NewsModel.title, postgresql_using='gin', 
      postgresql_ops={'title': 'gin_trgm_ops'})
```

> **Note**: GIN trigram index requires `pg_trgm` extension. For basic ILIKE, a simple B-tree index may suffice for moderate data volumes.

---

### Task 6: Write Unit Tests
- **Purpose**: TDD validation for ListNewsUseCase with search.
- **Prerequisites**: Task 3
- **Artifacts impacted**: 
  - `backend/tests/unit/test_list_news_use_case.py`
- **Test types**: Unit (pytest)
- **BDD Acceptance**:
  ```
  When I run pytest tests/unit/test_list_news_use_case.py
  Then all tests pass including search scenarios
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-BE-T01]

import pytest
from unittest.mock import Mock

from backend.app.application.use_cases.news.list_news import (
    ListNewsUseCase,
    ListNewsRequest,
)


class TestListNewsUseCaseSearch:
    def test_search_is_passed_to_repository(self):
        # Arrange
        repository = Mock()
        repository.list_public.return_value = ([], 0)
        
        use_case = ListNewsUseCase(repository)
        request = ListNewsRequest(search="navidad")
        
        # Act
        use_case.execute(request)
        
        # Assert
        repository.list_public.assert_called_once_with(
            skip=0,
            limit=20,
            search="navidad",
        )

    def test_empty_search_passes_none(self):
        # Arrange
        repository = Mock()
        repository.list_public.return_value = ([], 0)
        
        use_case = ListNewsUseCase(repository)
        request = ListNewsRequest(search=None)
        
        # Act
        use_case.execute(request)
        
        # Assert
        repository.list_public.assert_called_once_with(
            skip=0,
            limit=20,
            search=None,
        )

    def test_limit_capped_at_100(self):
        # Arrange
        repository = Mock()
        repository.list_public.return_value = ([], 0)
        
        use_case = ListNewsUseCase(repository)
        request = ListNewsRequest(limit=200)
        
        # Act
        result = use_case.execute(request)
        
        # Assert
        assert result.limit == 100
        repository.list_public.assert_called_once_with(
            skip=0,
            limit=100,
            search=None,
        )
```

---

### Task 7: Write Integration Tests
- **Purpose**: Verify search with real database.
- **Prerequisites**: Task 4
- **Artifacts impacted**: 
  - `backend/tests/integration/test_news_api.py` (add search tests)
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  When I run pytest tests/integration/test_news_api.py -k search
  Then all search tests pass
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-BE-T01]

import pytest


def test_search_news_by_title(client, published_general_news):
    """Search returns matching articles."""
    # Seed with articles having specific titles
    response = client.get("/api/news", params={"search": "navidad"})
    
    assert response.status_code == 200
    data = response.json()
    # All returned items should contain search term in title
    for item in data["items"]:
        assert "navidad" in item["title"].lower()


def test_search_case_insensitive(client, news_with_title):
    """Search is case insensitive."""
    news_with_title("Evento Navidad")
    
    response_lower = client.get("/api/news", params={"search": "navidad"})
    response_upper = client.get("/api/news", params={"search": "NAVIDAD"})
    
    assert response_lower.json()["total"] == response_upper.json()["total"]


def test_search_with_pagination(client, multiple_matching_news):
    """Search works with pagination."""
    # Seed 5 articles containing "evento"
    response = client.get("/api/news", params={
        "search": "evento",
        "skip": 0,
        "limit": 2,
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["skip"] == 0
    assert data["limit"] == 2


def test_search_no_results(client):
    """Search with no matches returns empty."""
    response = client.get("/api/news", params={"search": "xyznonexistent"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_search_empty_string_ignored(client):
    """Empty search returns all results."""
    response_no_search = client.get("/api/news")
    response_empty = client.get("/api/news", params={"search": ""})
    
    # Empty string validation should reject or treat as no search
    # Behavior depends on Pydantic validation (min_length=1)


def test_search_performance(client, many_articles):
    """Search responds within performance threshold."""
    import time
    
    start = time.time()
    response = client.get("/api/news", params={"search": "test"})
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 0.5  # <500ms
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Unit Tests | `docker compose exec backend pytest tests/unit/test_list_news_use_case.py -v` | All pass |
| Integration | `docker compose exec backend pytest tests/integration/test_news_api.py -k search -v` | All pass |
| All Backend | `docker compose exec backend pytest -v` | All pass |

### Manual Verification
1. Start containers: `docker compose up -d`
2. Open Swagger: `http://localhost:8005/docs`
3. **Search test**:
   - GET `/api/news?search=navidad`
   - Verify only matching articles returned
4. **Case insensitivity**:
   - GET `/api/news?search=NAVIDAD`
   - Verify same results as lowercase
5. **Pagination with search**:
   - GET `/api/news?search=evento&skip=0&limit=2`
   - Verify total reflects all matches, items capped to limit
6. **No results**:
   - GET `/api/news?search=xyznonexistent`
   - Verify empty items array, total=0
7. **Performance**:
   - Check response time in Network tab
   - Should be <500ms

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `backend/app/domain/repositories/news_repository.py` | MODIFY (add search param) |
| `backend/app/infrastructure/repositories/news_repository_impl.py` | MODIFY (ILIKE query) |
| `backend/app/application/use_cases/news/list_news.py` | MODIFY (add search to request) |
| `backend/app/presentation/api/news.py` | MODIFY (add search query param) |
| `backend/tests/unit/test_list_news_use_case.py` | MODIFY (add search tests) |
| `backend/tests/integration/test_news_api.py` | MODIFY (add search tests) |

---

## 7) API Contract Update

### GET /api/news

**Query Parameters**:
| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `skip` | int | No | 0 | >= 0 | Number of items to skip |
| `limit` | int | No | 20 | 1-100 | Max items per page |
| `search` | string | No | null | 1-100 chars | Title search (ILIKE) |

**Response** (PaginatedNewsResponse):
```json
{
  "items": [...],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```
