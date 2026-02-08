# NM-ADMIN-005-BE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-ADMIN-005-BE-T01**  
**Related user story**: **NM-ADMIN-005** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All tasks must include inline references to `NM-ADMIN-005-BE-T01`

---

## 1) Context & Objective

### Ticket Summary
Implement soft delete endpoint for news articles. Key requirements:
- `DELETE /api/news/{id}` — Sets `is_deleted=true` (no physical deletion)
- Admin-only access
- Audit logging with DELETE action
- Deleted articles excluded from all queries

**Business Value**: Administrators can remove content while preserving data for audit and potential recovery.

### Impacted Entities/Tables
| Entity | Layer | Operation |
|--------|-------|-----------|
| `DeleteNewsUseCase` | application/use_cases | CREATE |
| `NewsRepository` | domain/repositories | ADD `delete()` method |

### Impacted Services/Modules
| Layer | Module | Operation |
|-------|--------|-----------|
| Application | `application/use_cases/news/delete_news.py` | CREATE |
| Infrastructure | `infrastructure/repositories/news_repository_impl.py` | MODIFY (add soft_delete) |
| Presentation | `presentation/api/news.py` | MODIFY (add DELETE handler) |

### Impacted BDD Scenarios
This ticket implements:
- **"Successfully soft-delete an article"** — Set is_deleted=true, disappear from lists
- **"Deletion is logged for audit"** — Audit log entry with DELETE action

---

## 2) Scope

### In Scope
- DELETE `/api/news/{id}` endpoint (returns 204 No Content)
- `DeleteNewsUseCase` with soft delete logic
- Repository method `soft_delete()` or update `is_deleted` field
- Audit logging (log DELETE action with user_id and news_id)
- Admin-only access (403 for non-admin)
- 404 for non-existent or already-deleted articles
- Unit and integration tests

### Out of Scope
- Hard delete (permanent removal)
- Undo/Restore deleted articles
- Bulk delete

### Assumptions
1. **DB-T01 is complete**: News table has `is_deleted` boolean field
2. **Repository methods exist**: `get_by_id` already filters `is_deleted=False`
3. **Logging configured**: Python logging is available
4. **Admin auth exists**: `require_admin` dependency

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for DeleteNewsUseCase**:
   - Test successful soft delete sets is_deleted=true
   - Test error when article not found (404)
   - Test error when article already deleted (404)

2. **Integration tests for API**:
   - Test 204 response for successful delete
   - Test 403 for non-admin
   - Test 404 for non-existent article
   - Test article no longer returned by get_by_id

#### Phase 2: GREEN — Minimal Implementation
1. Add repository method
2. Create use case with audit logging
3. Add DELETE endpoint
4. Run tests to verify GREEN state

### 3.2 NFR Hooks

#### Security
- **RBAC**: Admin role check via dependency injection
- **Soft Delete**: Data preserved for audit

#### Observability
- **Audit Log**: Log level INFO with user_id, news_id, action="DELETE"

---

## 4) Atomic Task Breakdown

### Task 1: Add soft_delete Method to Repository
- **Purpose**: Repository method to set is_deleted=true.
- **Prerequisites**: Repository exists from BE-T01/T02
- **Artifacts impacted**: 
  - `backend/app/domain/repositories/news_repository.py`
  - `backend/app/infrastructure/repositories/news_repository_impl.py`
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  Given a news entity
  When I call repository.soft_delete(id)
  Then is_deleted is set to True
  And updated_at is refreshed
  ```

**Interface Addition**:
```python
# [Feature: News Management] [Story: NM-ADMIN-005] [Ticket: NM-ADMIN-005-BE-T01]

@abstractmethod
def soft_delete(self, id: UUID) -> bool:
    """Mark a news article as deleted. Returns True if successful."""
    pass
```

**Implementation**:
```python
# [Feature: News Management] [Story: NM-ADMIN-005] [Ticket: NM-ADMIN-005-BE-T01]

from datetime import datetime

def soft_delete(self, id: UUID) -> bool:
    model = self.db.query(NewsModel).filter(
        NewsModel.id == id,
        NewsModel.is_deleted == False
    ).first()
    
    if not model:
        return False
    
    model.is_deleted = True
    model.updated_at = datetime.utcnow()
    self.db.commit()
    return True
```

---

### Task 2: Create DeleteNewsUseCase
- **Purpose**: Orchestrate soft delete with audit logging.
- **Prerequisites**: Task 1
- **Artifacts impacted**: 
  - `backend/app/application/use_cases/news/delete_news.py`
  - `backend/app/application/use_cases/news/__init__.py`
- **Test types**: Unit (mocked repository)
- **BDD Acceptance**:
  ```
  # Scenario: Successfully soft-delete an article
  Given a valid article ID
  When I call DeleteNewsUseCase.execute(id, user_id)
  Then the article is soft deleted
  And an audit log is written
  
  # Scenario: Article not found
  Given non-existent article ID
  When I call DeleteNewsUseCase.execute(id, user_id)
  Then NotFoundException is raised
  ```

**Use Case Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-005] [Ticket: NM-ADMIN-005-BE-T01]

import logging
from uuid import UUID
from backend.app.domain.repositories.news_repository import NewsRepository
from backend.app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class DeleteNewsUseCase:
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def execute(self, news_id: UUID, deleted_by_user_id: UUID) -> None:
        # Attempt soft delete
        success = self.repository.soft_delete(news_id)
        
        if not success:
            raise NotFoundException(f"News article with id {news_id} not found")

        # Audit logging
        logger.info(
            "News article deleted",
            extra={
                "action": "DELETE",
                "news_id": str(news_id),
                "deleted_by": str(deleted_by_user_id),
            }
        )
```

---

### Task 3: Add DELETE Endpoint
- **Purpose**: Expose DELETE /api/news/{id} with Admin auth.
- **Prerequisites**: Tasks 1, 2
- **Artifacts impacted**: 
  - `backend/app/presentation/api/news.py`
- **Test types**: API integration
- **BDD Acceptance**:
  ```
  # Happy Path
  Given a valid article ID
  When I DELETE to /api/news/{id}
  Then I receive 204 No Content
  And the article is soft deleted
  
  # Security
  Given I am not an admin
  When I DELETE to /api/news/{id}
  Then I receive 403 Forbidden
  
  # Not Found
  Given non-existent article ID
  When I DELETE to /api/news/{id}
  Then I receive 404 Not Found
  ```

**Endpoint Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-005] [Ticket: NM-ADMIN-005-BE-T01]

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import require_admin
from backend.app.core.exceptions import NotFoundException
from backend.app.application.use_cases.news.delete_news import DeleteNewsUseCase
from backend.app.infrastructure.repositories.news_repository_impl import NewsRepositoryImpl


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news(
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Soft-delete a news article. Admin only."""
    repository = NewsRepositoryImpl(db)
    use_case = DeleteNewsUseCase(repository)
    
    try:
        use_case.execute(id, current_user.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

---

### Task 4: Write Unit Tests
- **Purpose**: TDD validation for DeleteNewsUseCase.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `backend/tests/unit/test_delete_news_use_case.py`
- **Test types**: Unit (pytest)
- **BDD Acceptance**:
  ```
  When I run pytest tests/unit/test_delete_news_use_case.py
  Then all tests pass
  And audit logging is verified
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-005] [Ticket: NM-ADMIN-005-BE-T01]

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from backend.app.application.use_cases.news.delete_news import DeleteNewsUseCase
from backend.app.core.exceptions import NotFoundException


class TestDeleteNewsUseCase:
    def test_delete_successfully(self):
        # Arrange
        news_id = uuid4()
        user_id = uuid4()
        repository = Mock()
        repository.soft_delete.return_value = True
        
        use_case = DeleteNewsUseCase(repository)
        
        # Act (should not raise)
        use_case.execute(news_id, user_id)
        
        # Assert
        repository.soft_delete.assert_called_once_with(news_id)

    def test_raises_not_found(self):
        # Arrange
        repository = Mock()
        repository.soft_delete.return_value = False
        
        use_case = DeleteNewsUseCase(repository)
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            use_case.execute(uuid4(), uuid4())

    def test_logs_delete_action(self):
        # Arrange
        news_id = uuid4()
        user_id = uuid4()
        repository = Mock()
        repository.soft_delete.return_value = True
        
        use_case = DeleteNewsUseCase(repository)
        
        # Act
        with patch('backend.app.application.use_cases.news.delete_news.logger') as mock_logger:
            use_case.execute(news_id, user_id)
            
            # Assert
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args
            assert call_kwargs[1]['extra']['action'] == 'DELETE'
            assert call_kwargs[1]['extra']['news_id'] == str(news_id)
```

---

### Task 5: Write Integration Tests
- **Purpose**: Verify API and repository work with real database.
- **Prerequisites**: Tasks 3, 4
- **Artifacts impacted**: 
  - `backend/tests/integration/test_news_api.py` (add delete tests)
  - `backend/tests/integration/test_news_repository.py` (add soft_delete test)
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  When I run pytest tests/integration/test_news_api.py -k delete
  Then all delete tests pass
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-005] [Ticket: NM-ADMIN-005-BE-T01]

def test_delete_news_success(client, admin_auth_headers, draft_news):
    """Test successful soft delete returns 204."""
    response = client.delete(
        f"/api/news/{draft_news.id}",
        headers=admin_auth_headers,
    )
    
    assert response.status_code == 204
    
    # Verify article no longer accessible
    get_response = client.get(
        f"/api/news/{draft_news.id}",
        headers=admin_auth_headers,
    )
    assert get_response.status_code == 404


def test_delete_news_forbidden_for_member(client, member_auth_headers, draft_news):
    """Test delete blocked for non-admin returns 403."""
    response = client.delete(
        f"/api/news/{draft_news.id}",
        headers=member_auth_headers,
    )
    
    assert response.status_code == 403


def test_delete_news_not_found(client, admin_auth_headers):
    """Test delete non-existent returns 404."""
    from uuid import uuid4
    response = client.delete(
        f"/api/news/{uuid4()}",
        headers=admin_auth_headers,
    )
    
    assert response.status_code == 404


def test_delete_already_deleted_returns_404(client, admin_auth_headers, draft_news):
    """Test deleting already-deleted article returns 404."""
    # First delete
    client.delete(f"/api/news/{draft_news.id}", headers=admin_auth_headers)
    
    # Second delete attempt
    response = client.delete(
        f"/api/news/{draft_news.id}",
        headers=admin_auth_headers,
    )
    
    assert response.status_code == 404
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Unit Tests | `docker compose exec backend pytest tests/unit/test_delete_news_use_case.py -v` | All pass |
| Integration (Repo) | `docker compose exec backend pytest tests/integration/test_news_repository.py -k soft_delete -v` | All pass |
| Integration (API) | `docker compose exec backend pytest tests/integration/test_news_api.py -k delete -v` | All pass |
| All Tests | `docker compose exec backend pytest -v` | All pass |

### Manual Verification
1. Start containers: `docker compose up -d`
2. Open Swagger: `http://localhost:8005/docs`
3. Create a news article (POST /api/news)
4. Delete the article (DELETE /api/news/{id}):
   - Verify 204 No Content response
5. Try to get the deleted article (GET /api/news/{id}):
   - Verify 404 Not Found
6. Check logs for audit entry:
   ```bash
   docker compose logs backend | grep DELETE
   ```
   - Verify log contains action="DELETE", news_id, deleted_by

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `backend/app/domain/repositories/news_repository.py` | MODIFY (add soft_delete) |
| `backend/app/infrastructure/repositories/news_repository_impl.py` | MODIFY (implement soft_delete) |
| `backend/app/application/use_cases/news/delete_news.py` | CREATE |
| `backend/app/application/use_cases/news/__init__.py` | MODIFY |
| `backend/app/presentation/api/news.py` | MODIFY (add DELETE handler) |
| `backend/tests/unit/test_delete_news_use_case.py` | CREATE |
| `backend/tests/integration/test_news_api.py` | MODIFY (add delete tests) |
| `backend/tests/integration/test_news_repository.py` | MODIFY (add soft_delete test) |

---

## 7) Audit Log Format

```json
{
  "level": "INFO",
  "message": "News article deleted",
  "extra": {
    "action": "DELETE",
    "news_id": "uuid-string",
    "deleted_by": "user-uuid-string"
  }
}
```
