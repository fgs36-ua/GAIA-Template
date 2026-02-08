# NM-ADMIN-003-BE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-ADMIN-003-BE-T01**  
**Related user story**: **NM-ADMIN-003** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All tasks must include inline references to `NM-ADMIN-003-BE-T01`

---

## 1) Context & Objective

### Ticket Summary
Implement the `POST /api/news/{id}/publish` action endpoint to transition an article from DRAFT to PUBLISHED status. Key requirements:
- Status transition: DRAFT → PUBLISHED only
- Sets `published_at` to current timestamp
- Business rule: summary is required to publish
- Admin-only access
- Performance: operation must complete <500ms

**Business Value**: Administrators can publish draft articles to make them visible to the appropriate audience (public or internal).

### Impacted Entities/Tables
| Entity | Layer | Operation |
|--------|-------|-----------|
| `NewsRepository` | domain/repositories | ADD method `publish()` or use `update()` |
| `PublishNewsUseCase` | application/use_cases | CREATE |

### Impacted Services/Modules
| Layer | Module | Operation |
|-------|--------|-----------|
| Domain | `domain/exceptions/news_exceptions.py` | CREATE |
| Application | `application/use_cases/news/publish_news.py` | CREATE |
| Infrastructure | `infrastructure/repositories/news_repository_impl.py` | MODIFY (status update) |
| Presentation | `presentation/api/news.py` | MODIFY (add publish action) |

### Impacted BDD Scenarios
This ticket implements:
- **"Successfully publish an article"** — Set PUBLISHED, set published_at
- **"Cannot publish without summary"** — Validation error
- **"Publication completes quickly"** — <500ms performance

---

## 2) Scope

### In Scope
- POST `/api/news/{id}/publish` action endpoint (returns 200 OK)
- `PublishNewsUseCase` with business logic
- Summary validation (400 error if missing)
- Status transition validation (only DRAFT can be published)
- Admin-only access (403 for non-admin)
- 404 for non-existent articles
- Unit and integration tests
- Performance target <500ms

### Out of Scope
- Scheduled publishing
- Notification system for new publications
- Publishing from ARCHIVED status

### Assumptions
1. **DB-T01 is complete**: News table and model exist
2. **BE-T01/T02 complete**: Repository with get_by_id and update exist
3. **Admin auth exists**: `require_admin` dependency

### Open Questions
1. **Q1**: Can an already-published article be "re-published"?
   - **Assumption**: No, return 400 "Article is already published"

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for PublishNewsUseCase**:
   - Test successful publish sets status to PUBLISHED
   - Test published_at is set to current time
   - Test error when article not found (404)
   - Test error when article already published (400)
   - Test error when summary is missing (400)

2. **Integration tests for API**:
   - Test 200 response on successful publish
   - Test 400 with missing summary
   - Test 400 when already published
   - Test 403 for non-admin
   - Test 404 for non-existent article

#### Phase 2: GREEN — Minimal Implementation
1. Create domain exceptions
2. Create use case
3. Add POST endpoint
4. Run tests to verify GREEN state

#### Phase 3: REFACTOR
1. Ensure consistent error handling
2. Add performance logging

### 3.2 NFR Hooks

#### Security
- **RBAC**: Admin role check via dependency injection
- **Authorization**: Validate article exists and is not deleted

#### Performance
- Target: <500ms for publish operation
- Log operation duration for monitoring

---

## 4) Atomic Task Breakdown

### Task 1: Create Domain Exceptions
- **Purpose**: Domain-specific exceptions for business rule violations. Clean architecture.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `backend/app/domain/exceptions/news_exceptions.py`
  - `backend/app/domain/exceptions/__init__.py`
- **Test types**: None (exception classes)
- **BDD Acceptance**:
  ```
  Given domain exceptions are defined
  When a business rule is violated
  Then the appropriate exception can be raised
  ```

**Exception Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-003] [Ticket: NM-ADMIN-003-BE-T01]

class NewsException(Exception):
    """Base exception for news domain."""
    pass


class NewsAlreadyPublishedException(NewsException):
    """Raised when attempting to publish an already published article."""
    def __init__(self, news_id):
        self.news_id = news_id
        super().__init__(f"News article {news_id} is already published")


class NewsMissingSummaryException(NewsException):
    """Raised when attempting to publish without a summary."""
    def __init__(self, news_id):
        self.news_id = news_id
        super().__init__(f"News article {news_id} requires a summary to publish")


class NewsInvalidStatusTransitionException(NewsException):
    """Raised when status transition is not allowed."""
    def __init__(self, news_id, current_status, target_status):
        self.news_id = news_id
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Cannot transition news {news_id} from {current_status} to {target_status}"
        )
```

---

### Task 2: Create PublishNewsUseCase
- **Purpose**: Orchestrate publish operation with business rules. Core application logic.
- **Prerequisites**: Task 1, repository methods from BE-T01/T02
- **Artifacts impacted**: 
  - `backend/app/application/use_cases/news/publish_news.py`
  - `backend/app/application/use_cases/news/__init__.py`
- **Test types**: Unit (mocked repository)
- **BDD Acceptance**:
  ```
  # Scenario: Successfully publish an article
  Given a DRAFT article with a summary
  When I call PublishNewsUseCase.execute(id)
  Then the article status is set to PUBLISHED
  And published_at is set to current time
  
  # Scenario: Cannot publish without summary
  Given a DRAFT article without a summary
  When I call PublishNewsUseCase.execute(id)
  Then NewsMissingSummaryException is raised
  
  # Scenario: Cannot re-publish
  Given a PUBLISHED article
  When I call PublishNewsUseCase.execute(id)
  Then NewsAlreadyPublishedException is raised
  ```

**Use Case Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-003] [Ticket: NM-ADMIN-003-BE-T01]

from datetime import datetime
from uuid import UUID
from backend.app.domain.entities.news import News, NewsStatus
from backend.app.domain.repositories.news_repository import NewsRepository
from backend.app.domain.exceptions.news_exceptions import (
    NewsAlreadyPublishedException,
    NewsMissingSummaryException,
    NewsInvalidStatusTransitionException,
)
from backend.app.core.exceptions import NotFoundException


class PublishNewsUseCase:
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def execute(self, news_id: UUID) -> News:
        # Fetch article
        news = self.repository.get_by_id(news_id)
        if not news:
            raise NotFoundException(f"News article with id {news_id} not found")

        # Business rule: Only DRAFT can be published
        if news.status == NewsStatus.PUBLISHED:
            raise NewsAlreadyPublishedException(news_id)
        
        if news.status != NewsStatus.DRAFT:
            raise NewsInvalidStatusTransitionException(
                news_id, news.status, NewsStatus.PUBLISHED
            )

        # Business rule: Summary is required
        if not news.summary or news.summary.strip() == '':
            raise NewsMissingSummaryException(news_id)

        # Update status and published_at
        news.status = NewsStatus.PUBLISHED
        news.published_at = datetime.utcnow()

        return self.repository.update(news)
```

---

### Task 3: Add publish() Method to Repository (Optional)
- **Purpose**: Repository method for status transitions. May reuse update().
- **Prerequisites**: Repository exists from BE-T01/T02
- **Artifacts impacted**: 
  - `backend/app/infrastructure/repositories/news_repository_impl.py`
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  Given news entity with updated status
  When I call repository.update(news)
  Then status and published_at are persisted
  ```

> **Note**: If `update()` already handles all fields including status and published_at, this task may be a no-op verification.

---

### Task 4: Add POST Publish Endpoint
- **Purpose**: Expose `/api/news/{id}/publish` with Admin auth. Presentation layer.
- **Prerequisites**: Tasks 1, 2
- **Artifacts impacted**: 
  - `backend/app/presentation/api/news.py`
- **Test types**: API integration
- **BDD Acceptance**:
  ```
  # Happy Path
  Given I am authenticated as an Administrator
  When I POST to /api/news/{id}/publish
  Then I receive 200 OK
  And the response contains the published article
  And published_at is set
  
  # Edge Case: No summary
  Given an article without summary
  When I POST to /api/news/{id}/publish
  Then I receive 400 Bad Request
  And message is "El resumen es obligatorio para publicar"
  
  # Security: Non-admin blocked
  Given I am authenticated as a Member
  When I POST to /api/news/{id}/publish
  Then I receive 403 Forbidden
  ```

**Endpoint Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-003] [Ticket: NM-ADMIN-003-BE-T01]

import time
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import require_admin
from backend.app.core.exceptions import NotFoundException
from backend.app.domain.exceptions.news_exceptions import (
    NewsAlreadyPublishedException,
    NewsMissingSummaryException,
    NewsInvalidStatusTransitionException,
)
from backend.app.application.use_cases.news.publish_news import PublishNewsUseCase
from backend.app.infrastructure.repositories.news_repository_impl import NewsRepositoryImpl
from backend.app.presentation.schemas.news import NewsResponse

logger = logging.getLogger(__name__)


@router.post("/{id}/publish", response_model=NewsResponse, status_code=status.HTTP_200_OK)
def publish_news(
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Publish a draft news article. Admin only."""
    start_time = time.time()
    
    repository = NewsRepositoryImpl(db)
    use_case = PublishNewsUseCase(repository)
    
    try:
        news = use_case.execute(id)
        
        # Performance logging
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Published news {id} in {duration_ms:.2f}ms")
        
        return NewsResponse.model_validate(news)
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NewsMissingSummaryException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El resumen es obligatorio para publicar"
        )
    except NewsAlreadyPublishedException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La noticia ya está publicada"
        )
    except NewsInvalidStatusTransitionException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

---

### Task 5: Write Unit Tests
- **Purpose**: TDD validation for PublishNewsUseCase. Supports `NM-ADMIN-003-BE-T01`.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `backend/tests/unit/test_publish_news_use_case.py`
- **Test types**: Unit (pytest)
- **BDD Acceptance**:
  ```
  Given the use case tests exist
  When I run pytest tests/unit/test_publish_news_use_case.py
  Then all tests pass
  And all business rules are verified
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-003] [Ticket: NM-ADMIN-003-BE-T01]

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime
from backend.app.application.use_cases.news.publish_news import PublishNewsUseCase
from backend.app.domain.entities.news import News, NewsStatus, NewsScope
from backend.app.domain.exceptions.news_exceptions import (
    NewsAlreadyPublishedException,
    NewsMissingSummaryException,
)
from backend.app.core.exceptions import NotFoundException


class TestPublishNewsUseCase:
    def test_publish_successfully(self):
        # Arrange
        news = News(
            id=uuid4(),
            title="Test Article",
            summary="Test summary",
            author_id=uuid4(),
            status=NewsStatus.DRAFT,
        )
        repository = Mock()
        repository.get_by_id.return_value = news
        repository.update.return_value = news
        
        use_case = PublishNewsUseCase(repository)
        
        # Act
        with patch('backend.app.application.use_cases.news.publish_news.datetime') as mock_dt:
            mock_dt.utcnow.return_value = datetime(2026, 2, 8, 12, 0, 0)
            result = use_case.execute(news.id)
        
        # Assert
        assert result.status == NewsStatus.PUBLISHED
        assert result.published_at == datetime(2026, 2, 8, 12, 0, 0)
        repository.update.assert_called_once()

    def test_raises_not_found(self):
        # Arrange
        repository = Mock()
        repository.get_by_id.return_value = None
        
        use_case = PublishNewsUseCase(repository)
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            use_case.execute(uuid4())

    def test_raises_already_published(self):
        # Arrange
        news = News(
            id=uuid4(),
            title="Test",
            summary="Summary",
            author_id=uuid4(),
            status=NewsStatus.PUBLISHED,
            published_at=datetime.utcnow(),
        )
        repository = Mock()
        repository.get_by_id.return_value = news
        
        use_case = PublishNewsUseCase(repository)
        
        # Act & Assert
        with pytest.raises(NewsAlreadyPublishedException):
            use_case.execute(news.id)

    def test_raises_missing_summary(self):
        # Arrange
        news = News(
            id=uuid4(),
            title="Test",
            summary=None,  # No summary
            author_id=uuid4(),
            status=NewsStatus.DRAFT,
        )
        repository = Mock()
        repository.get_by_id.return_value = news
        
        use_case = PublishNewsUseCase(repository)
        
        # Act & Assert
        with pytest.raises(NewsMissingSummaryException):
            use_case.execute(news.id)

    def test_raises_missing_summary_empty_string(self):
        # Arrange
        news = News(
            id=uuid4(),
            title="Test",
            summary="   ",  # Whitespace only
            author_id=uuid4(),
            status=NewsStatus.DRAFT,
        )
        repository = Mock()
        repository.get_by_id.return_value = news
        
        use_case = PublishNewsUseCase(repository)
        
        # Act & Assert
        with pytest.raises(NewsMissingSummaryException):
            use_case.execute(news.id)
```

---

### Task 6: Write Integration Tests
- **Purpose**: Verify API works with real database and returns correct status codes.
- **Prerequisites**: Tasks 4, 5
- **Artifacts impacted**: 
  - `backend/tests/integration/test_news_api.py` (add publish tests)
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  Given the integration tests exist
  When I run pytest tests/integration/test_news_api.py -k publish
  Then all publish tests pass
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-003] [Ticket: NM-ADMIN-003-BE-T01]

def test_publish_news_success(client, admin_auth_headers, draft_news_with_summary):
    """Test successful publish returns 200 and sets published_at."""
    response = client.post(
        f"/api/news/{draft_news_with_summary.id}/publish",
        headers=admin_auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PUBLISHED"
    assert data["published_at"] is not None


def test_publish_news_missing_summary(client, admin_auth_headers, draft_news_no_summary):
    """Test publish without summary returns 400."""
    response = client.post(
        f"/api/news/{draft_news_no_summary.id}/publish",
        headers=admin_auth_headers,
    )
    
    assert response.status_code == 400
    assert "resumen" in response.json()["detail"].lower()


def test_publish_news_already_published(client, admin_auth_headers, published_news):
    """Test publish already published returns 400."""
    response = client.post(
        f"/api/news/{published_news.id}/publish",
        headers=admin_auth_headers,
    )
    
    assert response.status_code == 400
    assert "ya está publicada" in response.json()["detail"]


def test_publish_news_forbidden_for_member(client, member_auth_headers, draft_news_with_summary):
    """Test publish blocked for non-admin returns 403."""
    response = client.post(
        f"/api/news/{draft_news_with_summary.id}/publish",
        headers=member_auth_headers,
    )
    
    assert response.status_code == 403


def test_publish_news_not_found(client, admin_auth_headers):
    """Test publish non-existent returns 404."""
    from uuid import uuid4
    response = client.post(
        f"/api/news/{uuid4()}/publish",
        headers=admin_auth_headers,
    )
    
    assert response.status_code == 404
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Unit Tests | `docker compose exec backend pytest tests/unit/test_publish_news_use_case.py -v` | All pass |
| Integration Tests | `docker compose exec backend pytest tests/integration/test_news_api.py -k publish -v` | All pass |
| All Tests | `docker compose exec backend pytest -v` | All pass |

### Manual Verification
1. Start containers: `docker compose up -d`
2. Open Swagger: `http://localhost:8005/docs`
3. Create a draft article with summary (POST /api/news)
4. Attempt to publish (POST /api/news/{id}/publish):
   - Verify 200 OK
   - Verify status is "PUBLISHED"
   - Verify published_at is set
5. Attempt to publish again:
   - Verify 400 "La noticia ya está publicada"
6. Create a draft article without summary
7. Attempt to publish:
   - Verify 400 "El resumen es obligatorio para publicar"
8. Check performance in logs:
   - Verify publish operation logged with duration <500ms

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `backend/app/domain/exceptions/news_exceptions.py` | CREATE |
| `backend/app/domain/exceptions/__init__.py` | CREATE or MODIFY |
| `backend/app/application/use_cases/news/publish_news.py` | CREATE |
| `backend/app/application/use_cases/news/__init__.py` | MODIFY |
| `backend/app/infrastructure/repositories/news_repository_impl.py` | VERIFY (update handles status) |
| `backend/app/presentation/api/news.py` | MODIFY (add publish endpoint) |
| `backend/tests/unit/test_publish_news_use_case.py` | CREATE |
| `backend/tests/integration/test_news_api.py` | MODIFY (add publish tests) |

---

## 7) Spanish Error Messages Summary

| Scenario | Message |
|----------|---------|
| Missing summary | "El resumen es obligatorio para publicar" |
| Already published | "La noticia ya está publicada" |
| Success (if needed at API level) | "Noticia publicada" |
