# NM-ADMIN-004-BE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-ADMIN-004-BE-T01**  
**Related user story**: **NM-ADMIN-004** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All tasks must include inline references to `NM-ADMIN-004-BE-T01`

---

## 1) Context & Objective

### Ticket Summary
Implement action endpoints to archive and restore news articles. Key requirements:
- **Archive**: `POST /api/news/{id}/archive` — PUBLISHED → ARCHIVED
- **Restore**: `POST /api/news/{id}/restore` — ARCHIVED → DRAFT (clears published_at)
- Admin-only access
- Status transition validation

**Business Value**: Administrators can hide outdated news from the public feed while retaining the content for future use.

### Impacted Entities/Tables
| Entity | Layer | Operation |
|--------|-------|-----------|
| `ArchiveNewsUseCase` | application/use_cases | CREATE |
| `RestoreNewsUseCase` | application/use_cases | CREATE |

### Impacted Services/Modules
| Layer | Module | Operation |
|-------|--------|-----------|
| Domain | `domain/exceptions/news_exceptions.py` | MODIFY (add exceptions) |
| Application | `application/use_cases/news/archive_news.py` | CREATE |
| Application | `application/use_cases/news/restore_news.py` | CREATE |
| Presentation | `presentation/api/news.py` | MODIFY (add endpoints) |

### Impacted BDD Scenarios
This ticket implements:
- **"Successfully archive an article"** — PUBLISHED → ARCHIVED
- **"Restore an archived article to draft"** — ARCHIVED → DRAFT, clear published_at

---

## 2) Scope

### In Scope
- POST `/api/news/{id}/archive` endpoint (200 OK)
- POST `/api/news/{id}/restore` endpoint (200 OK)
- `ArchiveNewsUseCase` with PUBLISHED-only validation
- `RestoreNewsUseCase` with ARCHIVED-only validation and published_at clearing
- Admin-only access (403 for non-admin)
- 404 for non-existent articles
- Unit and integration tests

### Out of Scope
- Bulk archive/restore
- Archive reason/notes
- Scheduled archival

### Assumptions
1. **DB-T01 is complete**: News table with status enum exists
2. **BE-T01/T02 complete**: Repository with get_by_id and update exist
3. **Admin auth exists**: `require_admin` dependency

### Open Questions
1. **Q1**: Can a DRAFT article be archived directly?
   - **Assumption**: No, only PUBLISHED can be archived (prevents data loss)
2. **Q2**: Should restore set a different timestamp (restored_at)?
   - **Assumption**: No additional timestamp needed; published_at is cleared

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for ArchiveNewsUseCase**:
   - Test successful archive sets status to ARCHIVED
   - Test error when article not PUBLISHED (400)
   - Test error when article not found (404)

2. **Unit tests for RestoreNewsUseCase**:
   - Test successful restore sets status to DRAFT
   - Test published_at is cleared
   - Test error when article not ARCHIVED (400)
   - Test error when article not found (404)

3. **Integration tests for API**:
   - Test 200 for archive on PUBLISHED article
   - Test 200 for restore on ARCHIVED article
   - Test 400 for invalid transitions
   - Test 403 for non-admin
   - Test 404 for non-existent article

#### Phase 2: GREEN — Minimal Implementation
1. Add domain exceptions
2. Create use cases
3. Add POST endpoints
4. Run tests to verify GREEN state

#### Phase 3: REFACTOR
1. Ensure consistent error handling
2. DRY up common status transition logic

### 3.2 NFR Hooks

#### Security
- **RBAC**: Admin role check via dependency injection

---

## 4) Atomic Task Breakdown

### Task 1: Add Domain Exceptions for Archive/Restore
- **Purpose**: Domain-specific exceptions for invalid status transitions.
- **Prerequisites**: news_exceptions.py exists from BE-T03
- **Artifacts impacted**: 
  - `backend/app/domain/exceptions/news_exceptions.py`
- **Test types**: None (exception classes)
- **BDD Acceptance**:
  ```
  Given domain exceptions are defined
  When an invalid status transition is attempted
  Then the appropriate exception can be raised
  ```

**Exception Additions**:
```python
# [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-BE-T01]

class NewsCannotBeArchivedException(NewsException):
    """Raised when attempting to archive a non-published article."""
    def __init__(self, news_id, current_status):
        self.news_id = news_id
        self.current_status = current_status
        super().__init__(
            f"Cannot archive news {news_id}: status is {current_status}, must be PUBLISHED"
        )


class NewsCannotBeRestoredException(NewsException):
    """Raised when attempting to restore a non-archived article."""
    def __init__(self, news_id, current_status):
        self.news_id = news_id
        self.current_status = current_status
        super().__init__(
            f"Cannot restore news {news_id}: status is {current_status}, must be ARCHIVED"
        )
```

---

### Task 2: Create ArchiveNewsUseCase
- **Purpose**: Orchestrate archive operation with status validation.
- **Prerequisites**: Task 1, repository from BE-T01/T02
- **Artifacts impacted**: 
  - `backend/app/application/use_cases/news/archive_news.py`
  - `backend/app/application/use_cases/news/__init__.py`
- **Test types**: Unit (mocked repository)
- **BDD Acceptance**:
  ```
  # Scenario: Successfully archive an article
  Given a PUBLISHED article
  When I call ArchiveNewsUseCase.execute(id)
  Then the article status is set to ARCHIVED
  
  # Scenario: Cannot archive non-published
  Given a DRAFT article
  When I call ArchiveNewsUseCase.execute(id)
  Then NewsCannotBeArchivedException is raised
  ```

**Use Case Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-BE-T01]

from uuid import UUID
from backend.app.domain.entities.news import News, NewsStatus
from backend.app.domain.repositories.news_repository import NewsRepository
from backend.app.domain.exceptions.news_exceptions import NewsCannotBeArchivedException
from backend.app.core.exceptions import NotFoundException


class ArchiveNewsUseCase:
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def execute(self, news_id: UUID) -> News:
        # Fetch article
        news = self.repository.get_by_id(news_id)
        if not news:
            raise NotFoundException(f"News article with id {news_id} not found")

        # Business rule: Only PUBLISHED can be archived
        if news.status != NewsStatus.PUBLISHED:
            raise NewsCannotBeArchivedException(news_id, news.status)

        # Update status
        news.status = NewsStatus.ARCHIVED
        # Note: published_at is retained for historical reference

        return self.repository.update(news)
```

---

### Task 3: Create RestoreNewsUseCase
- **Purpose**: Orchestrate restore operation, clear published_at.
- **Prerequisites**: Task 1, repository from BE-T01/T02
- **Artifacts impacted**: 
  - `backend/app/application/use_cases/news/restore_news.py`
  - `backend/app/application/use_cases/news/__init__.py`
- **Test types**: Unit (mocked repository)
- **BDD Acceptance**:
  ```
  # Scenario: Restore an archived article to draft
  Given an ARCHIVED article
  When I call RestoreNewsUseCase.execute(id)
  Then the article status is set to DRAFT
  And published_at is cleared (set to None)
  
  # Scenario: Cannot restore non-archived
  Given a PUBLISHED article
  When I call RestoreNewsUseCase.execute(id)
  Then NewsCannotBeRestoredException is raised
  ```

**Use Case Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-BE-T01]

from uuid import UUID
from backend.app.domain.entities.news import News, NewsStatus
from backend.app.domain.repositories.news_repository import NewsRepository
from backend.app.domain.exceptions.news_exceptions import NewsCannotBeRestoredException
from backend.app.core.exceptions import NotFoundException


class RestoreNewsUseCase:
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def execute(self, news_id: UUID) -> News:
        # Fetch article
        news = self.repository.get_by_id(news_id)
        if not news:
            raise NotFoundException(f"News article with id {news_id} not found")

        # Business rule: Only ARCHIVED can be restored
        if news.status != NewsStatus.ARCHIVED:
            raise NewsCannotBeRestoredException(news_id, news.status)

        # Update status and clear published_at
        news.status = NewsStatus.DRAFT
        news.published_at = None  # Clear publication timestamp

        return self.repository.update(news)
```

---

### Task 4: Add Archive Endpoint
- **Purpose**: Expose POST /api/news/{id}/archive with Admin auth.
- **Prerequisites**: Tasks 1, 2
- **Artifacts impacted**: 
  - `backend/app/presentation/api/news.py`
- **Test types**: API integration
- **BDD Acceptance**:
  ```
  # Happy Path
  Given a PUBLISHED article
  When I POST to /api/news/{id}/archive
  Then I receive 200 OK
  And status is "ARCHIVED"
  
  # Invalid Status
  Given a DRAFT article
  When I POST to /api/news/{id}/archive
  Then I receive 400 Bad Request
  ```

**Endpoint Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-BE-T01]

@router.post("/{id}/archive", response_model=NewsResponse, status_code=status.HTTP_200_OK)
def archive_news(
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Archive a published news article. Admin only."""
    repository = NewsRepositoryImpl(db)
    use_case = ArchiveNewsUseCase(repository)
    
    try:
        news = use_case.execute(id)
        return NewsResponse.model_validate(news)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NewsCannotBeArchivedException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden archivar noticias publicadas"
        )
```

---

### Task 5: Add Restore Endpoint
- **Purpose**: Expose POST /api/news/{id}/restore with Admin auth.
- **Prerequisites**: Tasks 1, 3
- **Artifacts impacted**: 
  - `backend/app/presentation/api/news.py`
- **Test types**: API integration
- **BDD Acceptance**:
  ```
  # Happy Path
  Given an ARCHIVED article
  When I POST to /api/news/{id}/restore
  Then I receive 200 OK
  And status is "DRAFT"
  And published_at is null
  
  # Invalid Status
  Given a PUBLISHED article
  When I POST to /api/news/{id}/restore
  Then I receive 400 Bad Request
  ```

**Endpoint Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-BE-T01]

@router.post("/{id}/restore", response_model=NewsResponse, status_code=status.HTTP_200_OK)
def restore_news(
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Restore an archived news article to draft. Admin only."""
    repository = NewsRepositoryImpl(db)
    use_case = RestoreNewsUseCase(repository)
    
    try:
        news = use_case.execute(id)
        return NewsResponse.model_validate(news)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NewsCannotBeRestoredException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden restaurar noticias archivadas"
        )
```

---

### Task 6: Write Unit Tests
- **Purpose**: TDD validation for both use cases.
- **Prerequisites**: Tasks 2, 3
- **Artifacts impacted**: 
  - `backend/tests/unit/test_archive_news_use_case.py`
  - `backend/tests/unit/test_restore_news_use_case.py`
- **Test types**: Unit (pytest)
- **BDD Acceptance**:
  ```
  When I run pytest tests/unit/test_archive_news_use_case.py tests/unit/test_restore_news_use_case.py
  Then all tests pass
  ```

**Test Template (Archive)**:
```python
# [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-BE-T01]

import pytest
from unittest.mock import Mock
from uuid import uuid4
from backend.app.application.use_cases.news.archive_news import ArchiveNewsUseCase
from backend.app.domain.entities.news import News, NewsStatus
from backend.app.domain.exceptions.news_exceptions import NewsCannotBeArchivedException
from backend.app.core.exceptions import NotFoundException


class TestArchiveNewsUseCase:
    def test_archive_successfully(self):
        # Arrange
        news = News(
            id=uuid4(),
            title="Test",
            author_id=uuid4(),
            status=NewsStatus.PUBLISHED,
        )
        repository = Mock()
        repository.get_by_id.return_value = news
        repository.update.return_value = news
        
        use_case = ArchiveNewsUseCase(repository)
        
        # Act
        result = use_case.execute(news.id)
        
        # Assert
        assert result.status == NewsStatus.ARCHIVED
        repository.update.assert_called_once()

    def test_raises_not_found(self):
        repository = Mock()
        repository.get_by_id.return_value = None
        
        use_case = ArchiveNewsUseCase(repository)
        
        with pytest.raises(NotFoundException):
            use_case.execute(uuid4())

    def test_raises_cannot_archive_draft(self):
        news = News(id=uuid4(), title="Test", author_id=uuid4(), status=NewsStatus.DRAFT)
        repository = Mock()
        repository.get_by_id.return_value = news
        
        use_case = ArchiveNewsUseCase(repository)
        
        with pytest.raises(NewsCannotBeArchivedException):
            use_case.execute(news.id)

    def test_raises_cannot_archive_already_archived(self):
        news = News(id=uuid4(), title="Test", author_id=uuid4(), status=NewsStatus.ARCHIVED)
        repository = Mock()
        repository.get_by_id.return_value = news
        
        use_case = ArchiveNewsUseCase(repository)
        
        with pytest.raises(NewsCannotBeArchivedException):
            use_case.execute(news.id)
```

**Test Template (Restore)**:
```python
# [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-BE-T01]

import pytest
from unittest.mock import Mock
from uuid import uuid4
from datetime import datetime
from backend.app.application.use_cases.news.restore_news import RestoreNewsUseCase
from backend.app.domain.entities.news import News, NewsStatus
from backend.app.domain.exceptions.news_exceptions import NewsCannotBeRestoredException
from backend.app.core.exceptions import NotFoundException


class TestRestoreNewsUseCase:
    def test_restore_successfully(self):
        news = News(
            id=uuid4(),
            title="Test",
            author_id=uuid4(),
            status=NewsStatus.ARCHIVED,
            published_at=datetime(2026, 1, 15),
        )
        repository = Mock()
        repository.get_by_id.return_value = news
        repository.update.return_value = news
        
        use_case = RestoreNewsUseCase(repository)
        
        result = use_case.execute(news.id)
        
        assert result.status == NewsStatus.DRAFT
        assert result.published_at is None  # Cleared
        repository.update.assert_called_once()

    def test_raises_not_found(self):
        repository = Mock()
        repository.get_by_id.return_value = None
        
        use_case = RestoreNewsUseCase(repository)
        
        with pytest.raises(NotFoundException):
            use_case.execute(uuid4())

    def test_raises_cannot_restore_published(self):
        news = News(id=uuid4(), title="Test", author_id=uuid4(), status=NewsStatus.PUBLISHED)
        repository = Mock()
        repository.get_by_id.return_value = news
        
        use_case = RestoreNewsUseCase(repository)
        
        with pytest.raises(NewsCannotBeRestoredException):
            use_case.execute(news.id)

    def test_raises_cannot_restore_draft(self):
        news = News(id=uuid4(), title="Test", author_id=uuid4(), status=NewsStatus.DRAFT)
        repository = Mock()
        repository.get_by_id.return_value = news
        
        use_case = RestoreNewsUseCase(repository)
        
        with pytest.raises(NewsCannotBeRestoredException):
            use_case.execute(news.id)
```

---

### Task 7: Write Integration Tests
- **Purpose**: Verify API endpoints work with real database.
- **Prerequisites**: Tasks 4, 5
- **Artifacts impacted**: 
  - `backend/tests/integration/test_news_api.py` (add archive/restore tests)
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  When I run pytest tests/integration/test_news_api.py -k "archive or restore"
  Then all archive/restore tests pass
  ```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Unit (Archive) | `docker compose exec backend pytest tests/unit/test_archive_news_use_case.py -v` | All pass |
| Unit (Restore) | `docker compose exec backend pytest tests/unit/test_restore_news_use_case.py -v` | All pass |
| Integration | `docker compose exec backend pytest tests/integration/test_news_api.py -k "archive or restore" -v` | All pass |
| All Tests | `docker compose exec backend pytest -v` | All pass |

### Manual Verification
1. Start containers: `docker compose up -d`
2. Open Swagger: `http://localhost:8005/docs`
3. **Archive Flow**:
   - Create an article → Publish it → Archive it
   - Verify status is "ARCHIVED"
   - Try to archive a DRAFT → Verify 400 error
4. **Restore Flow**:
   - Restore the archived article
   - Verify status is "DRAFT"
   - Verify published_at is null
   - Try to restore a PUBLISHED → Verify 400 error

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `backend/app/domain/exceptions/news_exceptions.py` | MODIFY (add 2 exceptions) |
| `backend/app/application/use_cases/news/archive_news.py` | CREATE |
| `backend/app/application/use_cases/news/restore_news.py` | CREATE |
| `backend/app/application/use_cases/news/__init__.py` | MODIFY |
| `backend/app/presentation/api/news.py` | MODIFY (add 2 endpoints) |
| `backend/tests/unit/test_archive_news_use_case.py` | CREATE |
| `backend/tests/unit/test_restore_news_use_case.py` | CREATE |
| `backend/tests/integration/test_news_api.py` | MODIFY (add archive/restore tests) |

---

## 7) Spanish Error Messages Summary

| Scenario | Message |
|----------|---------|
| Archive non-published | "Solo se pueden archivar noticias publicadas" |
| Restore non-archived | "Solo se pueden restaurar noticias archivadas" |
| Success (FE will use) | "Noticia archivada" / "Noticia restaurada a borrador" |

---

## 8) State Transition Diagram

```
┌─────────┐    publish()    ┌───────────┐    archive()    ┌──────────┐
│  DRAFT  │ ───────────────▶│ PUBLISHED │ ───────────────▶│ ARCHIVED │
└─────────┘                 └───────────┘                 └──────────┘
    ▲                                                          │
    │                                                          │
    └──────────────────── restore() ───────────────────────────┘
                     (clears published_at)
```
