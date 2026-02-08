# NM-PUBLIC-001-BE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-PUBLIC-001-BE-T01**  
**Related user story**: **NM-PUBLIC-001** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All tasks must include inline references to `NM-PUBLIC-001-BE-T01`

---

## 1) Context & Objective

### Ticket Summary
Implement public news list endpoint. Key requirements:
- `GET /api/news` — List published news articles
- Unauthenticated users see only GENERAL + PUBLISHED articles
- Members see GENERAL + INTERNAL (PUBLISHED)
- Admins see ALL (any status, any scope)
- Offset pagination (skip/limit)
- Sorted by `published_at` DESC (newest first)

**Business Value**: Visitors and members can browse news, with appropriate scope filtering based on their access level.

### Impacted Entities/Tables
| Entity | Layer | Operation |
|--------|-------|-----------|
| `ListNewsUseCase` | application/use_cases | CREATE |
| `NewsRepository` | domain/repositories | ADD `list_published()` method |

### Impacted Services/Modules
| Layer | Module | Operation |
|-------|--------|-----------|
| Application | `application/use_cases/news/list_news.py` | CREATE |
| Infrastructure | `infrastructure/repositories/news_repository_impl.py` | MODIFY (add list methods) |
| Presentation | `presentation/api/news.py` | MODIFY (add GET list handler) |
| Presentation | `presentation/schemas/news.py` | MODIFY (add paginated response) |

### Impacted BDD Scenarios
This ticket implements:
- **"Visitor can view general news"** — See GENERAL + PUBLISHED
- **"Supporter can view general news"** — Same as Visitor
- **"Empty news list"** — Return empty list with message hint

---

## 2) Scope

### In Scope
- GET `/api/news` endpoint with query parameters
- Query params: `skip` (default 0), `limit` (default 20, max 100)
- User role detection for scope filtering:
  - Anonymous/Supporter: GENERAL + PUBLISHED
  - Member: INTERNAL + GENERAL + PUBLISHED
  - Admin: All articles (any status, any scope)
- Sorted by `published_at` DESC
- Response includes total count for pagination UI
- Unit and integration tests
- Performance target: <500ms p95

### Out of Scope
- Cursor pagination
- Search by title (NM-PUBLIC-002)
- Scope filter tabs (NM-PUBLIC-002)

### Assumptions
1. **DB-T01 is complete**: News table exists with status, scope, is_deleted
2. **Auth optional**: Endpoint works for both authenticated and anonymous
3. **Optional current_user**: Use `get_current_user_optional` dependency

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for ListNewsUseCase**:
   - Test returns only PUBLISHED for anonymous
   - Test returns only GENERAL for non-members
   - Test returns INTERNAL+GENERAL for members
   - Test returns ALL for admins
   - Test pagination (skip/limit)

2. **Integration tests for API**:
   - Test anonymous sees GENERAL+PUBLISHED
   - Test member sees INTERNAL+GENERAL+PUBLISHED
   - Test admin sees drafts/archived
   - Test pagination params
   - Test sorting (newest first)

#### Phase 2: GREEN — Minimal Implementation
1. Add repository list methods
2. Create use case with role-based filtering
3. Add GET endpoint with optional auth
4. Run tests to verify GREEN state

### 3.2 NFR Hooks

#### Security
- No sensitive data leakage (is_deleted articles never shown to non-admins)
- Scope-based access control enforced server-side

#### Performance
- Database query optimized with proper indexes
- Pagination to limit result size

---

## 4) Atomic Task Breakdown

### Task 1: Add list Methods to Repository
- **Purpose**: Query news with filters for status, scope, and soft delete.
- **Prerequisites**: Repository exists from BE-T01
- **Artifacts impacted**: 
  - `backend/app/domain/repositories/news_repository.py`
  - `backend/app/infrastructure/repositories/news_repository_impl.py`
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  Given published news with various scopes
  When I call repository.list_public(skip, limit)
  Then I get only PUBLISHED + GENERAL articles
  And results are sorted by published_at DESC
  ```

**Interface Addition**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T01]

from typing import Tuple, List
from uuid import UUID

@abstractmethod
def list_public(
    self, 
    skip: int = 0, 
    limit: int = 20
) -> Tuple[List['News'], int]:
    """List PUBLISHED + GENERAL articles. Returns (items, total_count)."""
    pass

@abstractmethod
def list_for_member(
    self, 
    skip: int = 0, 
    limit: int = 20
) -> Tuple[List['News'], int]:
    """List PUBLISHED + (GENERAL or INTERNAL) articles. Returns (items, total_count)."""
    pass

@abstractmethod
def list_all(
    self, 
    skip: int = 0, 
    limit: int = 20,
    include_deleted: bool = False
) -> Tuple[List['News'], int]:
    """List ALL articles (admin view). Returns (items, total_count)."""
    pass
```

**Implementation**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T01]

from sqlalchemy import func, desc
from typing import Tuple, List

def list_public(self, skip: int = 0, limit: int = 20) -> Tuple[List[News], int]:
    query = self.db.query(NewsModel).filter(
        NewsModel.status == NewsStatus.PUBLISHED,
        NewsModel.scope == NewsScope.GENERAL,
        NewsModel.is_deleted == False
    ).order_by(desc(NewsModel.published_at))
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return [self._to_entity(m) for m in items], total

def list_for_member(self, skip: int = 0, limit: int = 20) -> Tuple[List[News], int]:
    query = self.db.query(NewsModel).filter(
        NewsModel.status == NewsStatus.PUBLISHED,
        NewsModel.scope.in_([NewsScope.GENERAL, NewsScope.INTERNAL]),
        NewsModel.is_deleted == False
    ).order_by(desc(NewsModel.published_at))
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return [self._to_entity(m) for m in items], total

def list_all(
    self, 
    skip: int = 0, 
    limit: int = 20,
    include_deleted: bool = False
) -> Tuple[List[News], int]:
    query = self.db.query(NewsModel)
    
    if not include_deleted:
        query = query.filter(NewsModel.is_deleted == False)
    
    query = query.order_by(
        desc(NewsModel.published_at.is_not(None)),  # Published first
        desc(NewsModel.published_at),
        desc(NewsModel.created_at)
    )
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return [self._to_entity(m) for m in items], total
```

---

### Task 2: Create Paginated Response Schema
- **Purpose**: Standard response format with items and pagination metadata.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `backend/app/presentation/schemas/news.py`
- **Test types**: Unit (schema validation)
- **BDD Acceptance**:
  ```
  Given a list response
  Then it includes items, total, skip, limit
  ```

**Schema Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T01]

from typing import List, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(description="List of items")
    total: int = Field(description="Total count of items")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Max items per page")
    
    @property
    def has_more(self) -> bool:
        return self.skip + len(self.items) < self.total


class NewsListItem(BaseModel):
    id: str
    title: str
    summary: str | None
    scope: str
    status: str
    cover_image_url: str | None
    published_at: str | None
    author_id: str
    created_at: str
    
    class Config:
        from_attributes = True


class NewsListResponse(PaginatedResponse[NewsListItem]):
    """Paginated list of news articles."""
    pass
```

---

### Task 3: Create ListNewsUseCase
- **Purpose**: Orchestrate list query with role-based filtering.
- **Prerequisites**: Tasks 1, 2
- **Artifacts impacted**: 
  - `backend/app/application/use_cases/news/list_news.py`
  - `backend/app/application/use_cases/news/__init__.py`
- **Test types**: Unit (mocked repository)
- **BDD Acceptance**:
  ```
  # Scenario: Anonymous user
  Given no user is authenticated
  When I call ListNewsUseCase.execute()
  Then I get only GENERAL + PUBLISHED articles
  
  # Scenario: Member
  Given a Member is authenticated
  When I call ListNewsUseCase.execute()
  Then I get GENERAL + INTERNAL + PUBLISHED articles
  
  # Scenario: Admin
  Given an Admin is authenticated
  When I call ListNewsUseCase.execute()
  Then I get ALL articles
  ```

**Use Case Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T01]

from dataclasses import dataclass
from typing import List, Tuple, Optional
from uuid import UUID
from backend.app.domain.repositories.news_repository import NewsRepository
from backend.app.domain.entities.user import User, UserRole


@dataclass
class ListNewsRequest:
    skip: int = 0
    limit: int = 20
    current_user: Optional[User] = None


@dataclass 
class NewsListDTO:
    id: UUID
    title: str
    summary: Optional[str]
    scope: str
    status: str
    cover_image_url: Optional[str]
    published_at: Optional[str]
    author_id: UUID
    created_at: str


class ListNewsUseCase:
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def execute(self, request: ListNewsRequest) -> Tuple[List[NewsListDTO], int]:
        # Clamp limit to max 100
        limit = min(request.limit, 100)
        skip = max(request.skip, 0)
        
        user = request.current_user
        
        # Determine which list method to use based on role
        if user is None:
            # Anonymous: public only
            items, total = self.repository.list_public(skip, limit)
        elif user.role == UserRole.ADMIN:
            # Admin: see everything
            items, total = self.repository.list_all(skip, limit)
        elif user.role == UserRole.MEMBER:
            # Member: public + internal
            items, total = self.repository.list_for_member(skip, limit)
        else:
            # Supporter: public only (same as anonymous)
            items, total = self.repository.list_public(skip, limit)
        
        # Map to DTOs
        dtos = [
            NewsListDTO(
                id=item.id,
                title=item.title,
                summary=item.summary,
                scope=item.scope.value,
                status=item.status.value,
                cover_image_url=item.cover_image_url,
                published_at=item.published_at.isoformat() if item.published_at else None,
                author_id=item.author_id,
                created_at=item.created_at.isoformat(),
            )
            for item in items
        ]
        
        return dtos, total
```

---

### Task 4: Add GET List Endpoint
- **Purpose**: Expose GET /api/news with optional auth.
- **Prerequisites**: Task 3
- **Artifacts impacted**: 
  - `backend/app/presentation/api/news.py`
- **Test types**: API integration
- **BDD Acceptance**:
  ```
  # Happy Path: Anonymous
  Given I am not authenticated
  When I GET /api/news
  Then I receive 200 with GENERAL + PUBLISHED articles
  
  # Happy Path: Member
  Given I am authenticated as Member
  When I GET /api/news
  Then I receive 200 with GENERAL + INTERNAL + PUBLISHED
  
  # Pagination
  When I GET /api/news?skip=10&limit=5
  Then I receive at most 5 items starting from position 10
  ```

**Endpoint Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T01]

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_optional
from backend.app.application.use_cases.news.list_news import ListNewsUseCase, ListNewsRequest
from backend.app.infrastructure.repositories.news_repository_impl import NewsRepositoryImpl
from backend.app.presentation.schemas.news import NewsListResponse, NewsListItem


@router.get("", response_model=NewsListResponse)
def list_news(
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max items per page"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    """
    List news articles.
    
    - Anonymous/Supporter: Returns GENERAL + PUBLISHED articles
    - Member: Returns GENERAL + INTERNAL + PUBLISHED articles  
    - Admin: Returns ALL articles (any status)
    
    Results sorted by published_at DESC (newest first).
    """
    repository = NewsRepositoryImpl(db)
    use_case = ListNewsUseCase(repository)
    
    request = ListNewsRequest(
        skip=skip,
        limit=limit,
        current_user=current_user,
    )
    
    items, total = use_case.execute(request)
    
    return NewsListResponse(
        items=[NewsListItem(**item.__dict__) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )
```

---

### Task 5: Write Unit Tests
- **Purpose**: TDD validation for ListNewsUseCase.
- **Prerequisites**: Task 3
- **Artifacts impacted**: 
  - `backend/tests/unit/test_list_news_use_case.py`
- **Test types**: Unit (pytest)
- **BDD Acceptance**:
  ```
  When I run pytest tests/unit/test_list_news_use_case.py
  Then all tests pass with role-based filtering verified
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T01]

import pytest
from unittest.mock import Mock
from uuid import uuid4
from backend.app.application.use_cases.news.list_news import (
    ListNewsUseCase, 
    ListNewsRequest
)
from backend.app.domain.entities.user import User, UserRole


class TestListNewsUseCase:
    def test_anonymous_user_gets_public_only(self):
        # Arrange
        repository = Mock()
        repository.list_public.return_value = ([], 0)
        
        use_case = ListNewsUseCase(repository)
        request = ListNewsRequest(current_user=None)
        
        # Act
        use_case.execute(request)
        
        # Assert
        repository.list_public.assert_called_once()
        repository.list_for_member.assert_not_called()
        repository.list_all.assert_not_called()

    def test_member_gets_public_and_internal(self):
        # Arrange
        repository = Mock()
        repository.list_for_member.return_value = ([], 0)
        member = User(id=uuid4(), role=UserRole.MEMBER)
        
        use_case = ListNewsUseCase(repository)
        request = ListNewsRequest(current_user=member)
        
        # Act
        use_case.execute(request)
        
        # Assert
        repository.list_for_member.assert_called_once()

    def test_admin_gets_all(self):
        # Arrange
        repository = Mock()
        repository.list_all.return_value = ([], 0)
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        
        use_case = ListNewsUseCase(repository)
        request = ListNewsRequest(current_user=admin)
        
        # Act
        use_case.execute(request)
        
        # Assert
        repository.list_all.assert_called_once()

    def test_limit_clamped_to_100(self):
        # Arrange
        repository = Mock()
        repository.list_public.return_value = ([], 0)
        
        use_case = ListNewsUseCase(repository)
        request = ListNewsRequest(limit=500)  # Over max
        
        # Act
        use_case.execute(request)
        
        # Assert
        repository.list_public.assert_called_with(0, 100)  # Clamped
```

---

### Task 6: Write Integration Tests
- **Purpose**: Verify API with real database.
- **Prerequisites**: Tasks 4, 5
- **Artifacts impacted**: 
  - `backend/tests/integration/test_news_api.py` (add list tests)
  - `backend/tests/integration/test_news_repository.py` (add list tests)
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  When I run pytest tests/integration/test_news_api.py -k list
  Then all list tests pass
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T01]

def test_list_news_anonymous_sees_general_only(client, published_general_news, published_internal_news):
    """Anonymous users only see GENERAL + PUBLISHED articles."""
    response = client.get("/api/news")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should include general, not internal
    assert data["total"] == 1
    assert data["items"][0]["id"] == str(published_general_news.id)
    assert data["items"][0]["scope"] == "GENERAL"


def test_list_news_member_sees_internal(client, member_auth_headers, published_general_news, published_internal_news):
    """Members see both GENERAL and INTERNAL PUBLISHED articles."""
    response = client.get("/api/news", headers=member_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 2
    scopes = {item["scope"] for item in data["items"]}
    assert scopes == {"GENERAL", "INTERNAL"}


def test_list_news_admin_sees_drafts(client, admin_auth_headers, draft_news, published_general_news):
    """Admins see all articles including drafts."""
    response = client.get("/api/news", headers=admin_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    statuses = {item["status"] for item in data["items"]}
    assert "DRAFT" in statuses
    assert "PUBLISHED" in statuses


def test_list_news_pagination(client, many_published_news):
    """Test pagination with skip and limit."""
    response = client.get("/api/news?skip=2&limit=3")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["items"]) == 3
    assert data["skip"] == 2
    assert data["limit"] == 3


def test_list_news_empty_returns_empty_list(client):
    """Empty database returns empty list, not error."""
    response = client.get("/api/news")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["items"] == []
    assert data["total"] == 0
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Unit Tests | `docker compose exec backend pytest tests/unit/test_list_news_use_case.py -v` | All pass |
| Integration (Repo) | `docker compose exec backend pytest tests/integration/test_news_repository.py -k list -v` | All pass |
| Integration (API) | `docker compose exec backend pytest tests/integration/test_news_api.py -k list -v` | All pass |
| All Tests | `docker compose exec backend pytest -v` | All pass |

### Manual Verification
1. Start containers: `docker compose up -d`
2. Open Swagger: `http://localhost:8005/docs`
3. **Anonymous test**:
   - GET `/api/news` without auth
   - Verify only GENERAL + PUBLISHED returned
4. **Member test**:
   - Login as member
   - GET `/api/news` with auth
   - Verify INTERNAL articles included
5. **Admin test**:
   - Login as admin
   - GET `/api/news` with auth
   - Verify DRAFT articles included
6. **Pagination test**:
   - GET `/api/news?skip=0&limit=5`
   - Verify response has correct skip/limit/total
7. **Performance check**:
   ```bash
   time curl http://localhost:8005/api/news
   ```
   - Verify < 500ms response

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `backend/app/domain/repositories/news_repository.py` | MODIFY (add list methods) |
| `backend/app/infrastructure/repositories/news_repository_impl.py` | MODIFY (implement list methods) |
| `backend/app/application/use_cases/news/list_news.py` | CREATE |
| `backend/app/application/use_cases/news/__init__.py` | MODIFY |
| `backend/app/presentation/schemas/news.py` | MODIFY (add paginated response) |
| `backend/app/presentation/api/news.py` | MODIFY (add GET list handler) |
| `backend/tests/unit/test_list_news_use_case.py` | CREATE |
| `backend/tests/integration/test_news_api.py` | MODIFY (add list tests) |
| `backend/tests/integration/test_news_repository.py` | MODIFY (add list tests) |

---

## 7) API Response Example

```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Reunión de Vecinos",
      "summary": "Convocatoria para la reunión mensual...",
      "scope": "GENERAL",
      "status": "PUBLISHED",
      "cover_image_url": "/uploads/news/reunion.jpg",
      "published_at": "2026-02-08T10:30:00Z",
      "author_id": "user-uuid",
      "created_at": "2026-02-07T09:00:00Z"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```

---

## 8) Role-Based Access Matrix

| User Role | Visible Scopes | Visible Statuses |
|-----------|----------------|------------------|
| Anonymous | GENERAL | PUBLISHED |
| Supporter | GENERAL | PUBLISHED |
| Member | GENERAL, INTERNAL | PUBLISHED |
| Admin | ALL | ALL |
