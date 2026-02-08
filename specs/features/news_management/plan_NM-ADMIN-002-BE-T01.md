# NM-ADMIN-002-BE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-ADMIN-002-BE-T01**  
**Related user story**: **NM-ADMIN-002** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All tasks must include inline references to `NM-ADMIN-002-BE-T01`

---

## 1) Context & Objective

### Ticket Summary
Implement the PUT `/api/news/{id}` endpoint to update an existing news article. Key requirements:
- Full article update (not partial PATCH)
- Preserve `published_at` timestamp for published articles
- Admin-only access with proper 403 handling
- XSS sanitization for content field (consistent with create)

**Business Value**: Enables Administrators to correct errors or update information in news articles before or after publication.

### Impacted Entities/Tables
| Entity | Layer | Operation |
|--------|-------|-----------|
| `NewsRepository` | domain/repositories | ADD method `update()`, `get_by_id()` |
| `UpdateNewsUseCase` | application/use_cases | CREATE |

### Impacted Services/Modules
| Layer | Module | Operation |
|-------|--------|-----------|
| Domain | `domain/repositories/news_repository.py` | MODIFY (add methods) |
| Application | `application/use_cases/news/update_news.py` | CREATE |
| Infrastructure | `infrastructure/repositories/news_repository_impl.py` | MODIFY |
| Presentation | `presentation/api/news.py` | MODIFY (add PUT handler) |
| Presentation | `presentation/schemas/news.py` | MODIFY (add UpdateNewsRequest) |

### Impacted BDD Scenarios
This ticket implements:
- **"Successfully edit a draft article"** — Update with new data, refresh updated_at
- **"Edit a published article"** — Preserve published_at timestamp
- **"Non-admin cannot access edit form"** — Return 403 Forbidden

---

## 2) Scope

### In Scope
- PUT `/api/news/{id}` endpoint (returns 200 OK)
- `UpdateNewsRequest` Pydantic schema (title, summary, content, scope)
- `UpdateNewsUseCase` with business logic
- `update()` and `get_by_id()` repository methods
- Admin-only access check
- XSS sanitization (same as create)
- Preserve `published_at` for published articles
- 404 for non-existent articles
- Unit and integration tests

### Out of Scope
- PATCH (partial updates)
- Status changes (handled by NM-ADMIN-003, NM-ADMIN-004, NM-ADMIN-005)
- Cover image upload
- Version conflict handling (optimistic locking)

### Assumptions
1. **BE-T01 is complete**: Create endpoint and repository exist
2. **News entity and model exist**: From DB-T01 and BE-T01
3. **Admin role check exists**: `require_admin` dependency

### Open Questions
1. **Q1**: Should we validate that the article is not deleted (`is_deleted=False`)?
   - **Assumption**: Yes, 404 if `is_deleted=True`

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for UpdateNewsUseCase**:
   - Test successful update with valid data
   - Test preserves published_at for published articles
   - Test updates updated_at timestamp
   - Test XSS sanitization of content
   - Test 404 when article not found

2. **Integration tests for NewsRepositoryImpl**:
   - Test get_by_id returns existing article
   - Test get_by_id returns None for deleted articles
   - Test update persists changes
   - Test update doesn't change published_at

3. **API tests for PUT /api/news/{id}**:
   - Test 200 response with valid admin auth
   - Test 401 without auth
   - Test 403 with non-admin auth
   - Test 404 for non-existent article
   - Test 422 with invalid payload

#### Phase 2: GREEN — Minimal Implementation
1. Add repository methods
2. Create use case
3. Add schema
4. Add PUT endpoint
5. Run tests to verify GREEN state

#### Phase 3: REFACTOR
1. Ensure consistent error handling
2. Add detailed logging

### 3.2 NFR Hooks

#### Security
- **RBAC**: Admin role check via dependency injection
- **XSS Prevention**: Sanitize HTML content with bleach
- **Authorization**: Only allow update if article exists and is not deleted

#### Observability
- Log update operations with user_id and news_id
- Audit trail via updated_at timestamp

---

## 4) Atomic Task Breakdown

### Task 1: Add Repository Methods (Interface)
- **Purpose**: Extend NewsRepository interface with get_by_id and update. Supports hexagonal architecture.
- **Prerequisites**: BE-T01 completed
- **Artifacts impacted**: 
  - `backend/app/domain/repositories/news_repository.py`
- **Test types**: None (interface only)
- **BDD Acceptance**:
  ```
  Given the NewsRepository interface
  When I add get_by_id and update methods
  Then they are defined as abstract methods
  ```

**Updated Interface**:
```python
# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from backend.app.domain.entities.news import News


class NewsRepository(ABC):
    @abstractmethod
    def create(self, news: News) -> News:
        """Persist a new news article."""
        pass

    @abstractmethod
    def get_by_id(self, id: UUID) -> Optional[News]:
        """Retrieve a news article by ID. Returns None if not found or deleted."""
        pass

    @abstractmethod
    def update(self, news: News) -> News:
        """Update an existing news article."""
        pass
```

---

### Task 2: Implement Repository Methods
- **Purpose**: Add get_by_id and update to NewsRepositoryImpl. Adapter layer.
- **Prerequisites**: Task 1
- **Artifacts impacted**: 
  - `backend/app/infrastructure/repositories/news_repository_impl.py`
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  Given an article exists in the database
  When I call repository.get_by_id(id)
  Then I receive the News entity
  
  Given an article with is_deleted=True
  When I call repository.get_by_id(id)
  Then I receive None
  
  Given a valid News entity with changes
  When I call repository.update(entity)
  Then the changes are persisted
  And updated_at is refreshed
  ```

**Implementation Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]

from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.domain.entities.news import News
from backend.app.domain.repositories.news_repository import NewsRepository
from backend.app.infrastructure.models.news import News as NewsModel
from backend.app.infrastructure.db.mappers.news_mapper import NewsMapper


class NewsRepositoryImpl(NewsRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, news: News) -> News:
        model = NewsMapper.to_model(news)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return NewsMapper.to_entity(model)

    def get_by_id(self, id: UUID) -> Optional[News]:
        model = self.db.query(NewsModel).filter(
            NewsModel.id == id,
            NewsModel.is_deleted == False
        ).first()
        return NewsMapper.to_entity(model) if model else None

    def update(self, news: News) -> News:
        model = self.db.query(NewsModel).filter(NewsModel.id == news.id).first()
        if not model:
            raise ValueError(f"News with id {news.id} not found")
        
        # Update fields
        model.title = news.title
        model.summary = news.summary
        model.content = news.content
        model.scope = news.scope
        model.cover_url = news.cover_url
        model.updated_at = datetime.utcnow()
        # Note: published_at is NOT updated here (preserved)
        
        self.db.commit()
        self.db.refresh(model)
        return NewsMapper.to_entity(model)
```

---

### Task 3: Create UpdateNewsUseCase
- **Purpose**: Orchestrate article update with business logic and XSS sanitization.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `backend/app/application/use_cases/news/update_news.py`
  - `backend/app/application/use_cases/news/__init__.py`
- **Test types**: Unit (mocked repository)
- **BDD Acceptance**:
  ```
  # Scenario: Successfully edit a draft article
  Given a valid article ID and update data
  When I call UpdateNewsUseCase.execute()
  Then the article is updated with the new data
  And updated_at is refreshed
  
  # Scenario: Edit a published article
  Given a published article
  When I update the content
  Then published_at is NOT changed
  And the article remains PUBLISHED
  
  # Scenario: Article not found
  Given a non-existent article ID
  When I call UpdateNewsUseCase.execute()
  Then a NotFoundException is raised
  ```

**Use Case Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]

import bleach
from uuid import UUID
from backend.app.domain.entities.news import News, NewsScope
from backend.app.domain.repositories.news_repository import NewsRepository
from backend.app.core.exceptions import NotFoundException

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'blockquote']
ALLOWED_ATTRS = {'a': ['href', 'title']}


class UpdateNewsUseCase:
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
        if scope:
            existing.scope = scope
        existing.cover_url = cover_url
        # Note: status and published_at are NOT modified

        return self.repository.update(existing)
```

---

### Task 4: Add UpdateNewsRequest Schema
- **Purpose**: Define request DTO for update endpoint. Pydantic validation.
- **Prerequisites**: BE-T01 schemas exist
- **Artifacts impacted**: 
  - `backend/app/presentation/schemas/news.py`
- **Test types**: Unit (schema validation)
- **BDD Acceptance**:
  ```
  Given an UpdateNewsRequest with valid data
  When Pydantic validates the request
  Then validation passes
  
  Given an UpdateNewsRequest without title
  When Pydantic validates the request
  Then a validation error is raised
  ```

**Schema Addition**:
```python
# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]

class UpdateNewsRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Article headline")
    summary: Optional[str] = Field(None, max_length=500, description="Brief description")
    content: Optional[str] = Field(None, description="Rich text content (HTML)")
    scope: Optional[NewsScope] = Field(None, description="Visibility scope")
    cover_url: Optional[str] = Field(None, max_length=2048, description="Cover image URL")

    model_config = ConfigDict(extra="forbid")
```

---

### Task 5: Add PUT Endpoint to Router
- **Purpose**: Expose PUT /api/news/{id} with Admin auth. Presentation layer.
- **Prerequisites**: Tasks 2, 3, 4
- **Artifacts impacted**: 
  - `backend/app/presentation/api/news.py`
- **Test types**: API integration
- **BDD Acceptance**:
  ```
  # Happy Path
  Given I am authenticated as an Administrator
  When I PUT to /api/news/{id} with valid data
  Then I receive 200 OK
  And the response contains the updated article
  
  # Security: Non-admin blocked
  Given I am authenticated as a Member
  When I PUT to /api/news/{id}
  Then I receive 403 Forbidden
  
  # Not Found
  Given an invalid article ID
  When I PUT to /api/news/{id}
  Then I receive 404 Not Found
  ```

**Endpoint Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import require_admin
from backend.app.core.exceptions import NotFoundException
from backend.app.application.use_cases.news.update_news import UpdateNewsUseCase
from backend.app.infrastructure.repositories.news_repository_impl import NewsRepositoryImpl
from backend.app.presentation.schemas.news import UpdateNewsRequest, NewsResponse


@router.put("/{id}", response_model=NewsResponse, status_code=status.HTTP_200_OK)
def update_news(
    id: UUID,
    request: UpdateNewsRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Update an existing news article. Admin only."""
    repository = NewsRepositoryImpl(db)
    use_case = UpdateNewsUseCase(repository)
    
    try:
        news = use_case.execute(
            id=id,
            title=request.title,
            summary=request.summary,
            content=request.content,
            scope=request.scope,
            cover_url=request.cover_url,
        )
        return NewsResponse.model_validate(news)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

---

### Task 6: Create NotFoundException (if not exists)
- **Purpose**: Consistent exception handling for not found resources.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `backend/app/core/exceptions.py`
- **Test types**: None
- **BDD Acceptance**:
  ```
  Given NotFoundException is defined
  When I raise it in a use case
  Then it can be caught in the router
  And mapped to 404 status code
  ```

**Exception Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]

class NotFoundException(Exception):
    """Raised when a requested resource is not found."""
    pass
```

---

### Task 7: Write Unit Tests
- **Purpose**: TDD validation for UpdateNewsUseCase. Supports `NM-ADMIN-002-BE-T01`.
- **Prerequisites**: Task 3
- **Artifacts impacted**: 
  - `backend/tests/unit/test_update_news_use_case.py`
- **Test types**: Unit (Vitest)
- **BDD Acceptance**:
  ```
  Given the use case tests exist
  When I run pytest tests/unit/test_update_news_use_case.py
  Then all tests pass
  And XSS sanitization is verified
  And published_at preservation is verified
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-BE-T01]

import pytest
from unittest.mock import Mock
from uuid import uuid4
from datetime import datetime
from backend.app.application.use_cases.news.update_news import UpdateNewsUseCase
from backend.app.domain.entities.news import News, NewsStatus, NewsScope
from backend.app.core.exceptions import NotFoundException


class TestUpdateNewsUseCase:
    def test_update_successfully(self):
        # Arrange
        existing = News(
            id=uuid4(),
            title="Old Title",
            author_id=uuid4(),
            status=NewsStatus.DRAFT,
        )
        repository = Mock()
        repository.get_by_id.return_value = existing
        repository.update.return_value = existing
        
        use_case = UpdateNewsUseCase(repository)
        
        # Act
        result = use_case.execute(
            id=existing.id,
            title="New Title",
            summary="New summary",
        )
        
        # Assert
        assert result.title == "New Title"
        repository.update.assert_called_once()

    def test_preserves_published_at(self):
        # Arrange
        published_at = datetime(2026, 1, 15, 12, 0, 0)
        existing = News(
            id=uuid4(),
            title="Old Title",
            author_id=uuid4(),
            status=NewsStatus.PUBLISHED,
            published_at=published_at,
        )
        repository = Mock()
        repository.get_by_id.return_value = existing
        repository.update.return_value = existing
        
        use_case = UpdateNewsUseCase(repository)
        
        # Act
        use_case.execute(id=existing.id, title="New Title")
        
        # Assert
        updated_entity = repository.update.call_args[0][0]
        assert updated_entity.published_at == published_at  # Unchanged

    def test_sanitizes_xss_content(self):
        # Arrange
        existing = News(id=uuid4(), title="Test", author_id=uuid4())
        repository = Mock()
        repository.get_by_id.return_value = existing
        repository.update.return_value = existing
        
        use_case = UpdateNewsUseCase(repository)
        
        # Act
        use_case.execute(
            id=existing.id,
            title="Test",
            content="<p>Hello</p><script>alert('xss')</script>",
        )
        
        # Assert
        updated_entity = repository.update.call_args[0][0]
        assert "<script>" not in updated_entity.content

    def test_raises_not_found(self):
        # Arrange
        repository = Mock()
        repository.get_by_id.return_value = None
        
        use_case = UpdateNewsUseCase(repository)
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            use_case.execute(id=uuid4(), title="Test")
```

---

### Task 8: Write Integration Tests
- **Purpose**: Verify repository and API work with real database. Supports `NM-ADMIN-002-BE-T01`.
- **Prerequisites**: Tasks 2, 5
- **Artifacts impacted**: 
  - `backend/tests/integration/test_news_repository.py` (add update tests)
  - `backend/tests/integration/test_news_api.py` (add PUT tests)
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  Given the integration tests exist
  When I run pytest tests/integration/
  Then all update tests pass
  And the database reflects changes
  ```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Unit Tests | `docker compose exec backend pytest tests/unit/test_update_news_use_case.py -v` | All pass |
| Integration (Repo) | `docker compose exec backend pytest tests/integration/test_news_repository.py -v` | All pass |
| Integration (API) | `docker compose exec backend pytest tests/integration/test_news_api.py -v` | All pass |

### Manual Verification
1. Start containers: `docker compose up -d`
2. Open Swagger: `http://localhost:8005/docs`
3. Create a news article (POST /api/news)
4. Update the article (PUT /api/news/{id}) with:
   ```json
   {
     "title": "Updated Title",
     "summary": "Updated summary",
     "content": "<p>Updated content</p><script>xss</script>",
     "scope": "INTERNAL"
   }
   ```
5. Verify:
   - Response is 200 OK
   - Title and summary are updated
   - Content has script tag stripped
   - `updated_at` is refreshed
   - `published_at` is unchanged (if published)

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `backend/app/domain/repositories/news_repository.py` | MODIFY (add get_by_id, update) |
| `backend/app/infrastructure/repositories/news_repository_impl.py` | MODIFY (implement methods) |
| `backend/app/application/use_cases/news/update_news.py` | CREATE |
| `backend/app/application/use_cases/news/__init__.py` | MODIFY |
| `backend/app/core/exceptions.py` | CREATE or MODIFY |
| `backend/app/presentation/schemas/news.py` | MODIFY (add UpdateNewsRequest) |
| `backend/app/presentation/api/news.py` | MODIFY (add PUT handler) |
| `backend/tests/unit/test_update_news_use_case.py` | CREATE |
| `backend/tests/integration/test_news_repository.py` | MODIFY |
| `backend/tests/integration/test_news_api.py` | MODIFY |
