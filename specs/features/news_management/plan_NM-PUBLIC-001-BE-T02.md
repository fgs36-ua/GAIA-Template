# NM-PUBLIC-001-BE-T02 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-PUBLIC-001-BE-T02**  
**Related user story**: **NM-PUBLIC-001** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All tasks must include inline references to `NM-PUBLIC-001-BE-T02`

---

## 1) Context & Objective

### Ticket Summary
Implement news detail endpoint with scope-based access control. Key requirements:
- `GET /api/news/{id}` — Returns full article detail
- Scope-based access:
  - GENERAL articles: accessible by anyone
  - INTERNAL articles: accessible only by Members and Admins
- 403 Forbidden for unauthorized access to INTERNAL
- 404 Not Found for deleted or non-existent articles
- Full content returned (not just summary)

**Business Value**: Users can read article details, with internal content protected for members only.

### Impacted Entities/Tables
| Entity | Layer | Operation |
|--------|-------|-----------|
| `GetNewsDetailUseCase` | application/use_cases | CREATE |
| `NewsRepository` | domain/repositories | ADD `get_by_id()` (if not exists) |

### Impacted Services/Modules
| Layer | Module | Operation |
|-------|--------|-----------|
| Application | `application/use_cases/news/get_news_detail.py` | CREATE |
| Presentation | `presentation/api/news.py` | MODIFY (add GET by ID handler) |
| Presentation | `presentation/schemas/news.py` | MODIFY (add detail response) |

### Impacted BDD Scenarios
This ticket implements:
- **"Visitor can view general news"** — Full content accessible
- **"Member can view internal news"** — Internal content protected

---

## 2) Scope

### In Scope
- GET `/api/news/{id}` endpoint
- `GetNewsDetailUseCase` with scope validation
- Response schema with full content
- 403 Forbidden for non-member accessing INTERNAL
- 404 Not Found for deleted or non-existent
- Non-published articles hidden from non-admins
- Unit and integration tests

### Out of Scope
- View tracking/analytics (future)
- Related articles
- Comments

### Assumptions
1. **DB-T01 is complete**: News table exists
2. **Repository get_by_id exists**: From previous tickets
3. **Auth optional**: Works for anonymous and authenticated

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for GetNewsDetailUseCase**:
   - Test returns GENERAL article to anyone
   - Test returns INTERNAL article to member
   - Test returns 403 for INTERNAL to anonymous
   - Test returns 404 for deleted article
   - Test returns 404 for non-existent

2. **Integration tests for API**:
   - Test 200 for GENERAL access
   - Test 200 for member accessing INTERNAL
   - Test 403 for anonymous accessing INTERNAL
   - Test 404 for non-existent ID
   - Test 404 for deleted article

#### Phase 2: GREEN — Minimal Implementation
1. Create domain exception
2. Create use case with scope checks
3. Add GET endpoint with optional auth
4. Run tests to verify GREEN state

### 3.2 NFR Hooks

#### Security
- Scope-based access control enforced server-side
- No information leakage (same 404 for deleted vs non-existent)

#### Performance
- Single database query (eager load author if needed)

---

## 4) Atomic Task Breakdown

### Task 1: Add News Access Exception
- **Purpose**: Domain exception for unauthorized scope access.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `backend/app/domain/exceptions/news.py`
- **Test types**: Unit
- **BDD Acceptance**:
  ```
  Given an INTERNAL article
  When non-member tries to access
  Then ForbiddenException is raised
  ```

**Exception Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T02]

class NewsAccessForbiddenException(Exception):
    """Raised when user doesn't have access to a news article's scope."""
    def __init__(self, message: str = "No tienes acceso a esta noticia"):
        self.message = message
        super().__init__(self.message)
```

---

### Task 2: Create News Detail Response Schema
- **Purpose**: Full article detail with content.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `backend/app/presentation/schemas/news.py`
- **Test types**: Unit (schema validation)
- **BDD Acceptance**:
  ```
  Given a news entity
  When I serialize to NewsDetailResponse
  Then all fields including content are present
  ```

**Schema Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T02]

from pydantic import BaseModel
from typing import Optional


class NewsDetailResponse(BaseModel):
    id: str
    title: str
    content: str
    summary: Optional[str] = None
    scope: str
    status: str
    cover_image_url: Optional[str] = None
    published_at: Optional[str] = None
    author_id: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
```

---

### Task 3: Create GetNewsDetailUseCase
- **Purpose**: Fetch article with scope-based access control.
- **Prerequisites**: Tasks 1, 2
- **Artifacts impacted**: 
  - `backend/app/application/use_cases/news/get_news_detail.py`
  - `backend/app/application/use_cases/news/__init__.py`
- **Test types**: Unit (mocked repository)
- **BDD Acceptance**:
  ```
  # Scenario: GENERAL article, anonymous
  Given a PUBLISHED GENERAL article
  When anonymous user calls GetNewsDetailUseCase
  Then the article is returned
  
  # Scenario: INTERNAL article, member
  Given a PUBLISHED INTERNAL article
  When Member calls GetNewsDetailUseCase
  Then the article is returned
  
  # Scenario: INTERNAL article, anonymous
  Given a PUBLISHED INTERNAL article
  When anonymous user calls GetNewsDetailUseCase
  Then ForbiddenException is raised
  
  # Scenario: Deleted article
  Given a deleted article
  When any user calls GetNewsDetailUseCase
  Then NotFoundException is raised
  
  # Scenario: DRAFT article, non-admin
  Given a DRAFT article
  When non-admin calls GetNewsDetailUseCase
  Then NotFoundException is raised (hidden)
  ```

**Use Case Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T02]

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from backend.app.domain.repositories.news_repository import NewsRepository
from backend.app.domain.entities.user import User, UserRole
from backend.app.domain.entities.news import NewsScope, NewsStatus
from backend.app.domain.exceptions.news import NewsAccessForbiddenException
from backend.app.core.exceptions import NotFoundException


@dataclass
class GetNewsDetailRequest:
    news_id: UUID
    current_user: Optional[User] = None


class GetNewsDetailUseCase:
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def execute(self, request: GetNewsDetailRequest):
        # Fetch article (includes deleted check in repository)
        article = self.repository.get_by_id(request.news_id)
        
        if article is None:
            raise NotFoundException(f"Noticia con id {request.news_id} no encontrada")
        
        user = request.current_user
        is_admin = user and user.role == UserRole.ADMIN
        is_member = user and user.role in [UserRole.MEMBER, UserRole.ADMIN]
        
        # Check if article is accessible
        # Admins see everything
        if is_admin:
            return article
        
        # Non-admins cannot see non-published articles
        if article.status != NewsStatus.PUBLISHED:
            raise NotFoundException(f"Noticia con id {request.news_id} no encontrada")
        
        # Check scope access
        if article.scope == NewsScope.INTERNAL and not is_member:
            raise NewsAccessForbiddenException(
                "Esta noticia es solo para socios"
            )
        
        return article
```

---

### Task 4: Add GET Detail Endpoint
- **Purpose**: Expose GET /api/news/{id} with optional auth.
- **Prerequisites**: Task 3
- **Artifacts impacted**: 
  - `backend/app/presentation/api/news.py`
- **Test types**: API integration
- **BDD Acceptance**:
  ```
  # Happy Path: GENERAL
  Given a PUBLISHED GENERAL article
  When I GET /api/news/{id}
  Then I receive 200 with full content
  
  # Happy Path: INTERNAL as member
  Given a PUBLISHED INTERNAL article
  When Member GETs /api/news/{id}
  Then I receive 200 with full content
  
  # Forbidden: INTERNAL as anonymous
  Given a PUBLISHED INTERNAL article  
  When anonymous GETs /api/news/{id}
  Then I receive 403 Forbidden
  
  # Not Found
  Given non-existent ID
  When I GET /api/news/{id}
  Then I receive 404 Not Found
  ```

**Endpoint Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T02]

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_optional
from backend.app.core.exceptions import NotFoundException
from backend.app.domain.exceptions.news import NewsAccessForbiddenException
from backend.app.application.use_cases.news.get_news_detail import (
    GetNewsDetailUseCase, 
    GetNewsDetailRequest
)
from backend.app.infrastructure.repositories.news_repository_impl import NewsRepositoryImpl
from backend.app.presentation.schemas.news import NewsDetailResponse


@router.get("/{id}", response_model=NewsDetailResponse)
def get_news_detail(
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    """
    Get news article detail.
    
    - GENERAL articles: accessible by anyone
    - INTERNAL articles: accessible only by Members and Admins
    
    Returns 403 for unauthorized access to INTERNAL scope.
    Returns 404 for non-existent or deleted articles.
    """
    repository = NewsRepositoryImpl(db)
    use_case = GetNewsDetailUseCase(repository)
    
    request = GetNewsDetailRequest(
        news_id=id,
        current_user=current_user,
    )
    
    try:
        article = use_case.execute(request)
        return NewsDetailResponse(
            id=str(article.id),
            title=article.title,
            content=article.content,
            summary=article.summary,
            scope=article.scope.value,
            status=article.status.value,
            cover_image_url=article.cover_image_url,
            published_at=article.published_at.isoformat() if article.published_at else None,
            author_id=str(article.author_id),
            created_at=article.created_at.isoformat(),
            updated_at=article.updated_at.isoformat(),
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NewsAccessForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
```

---

### Task 5: Write Unit Tests
- **Purpose**: TDD validation for GetNewsDetailUseCase.
- **Prerequisites**: Task 3
- **Artifacts impacted**: 
  - `backend/tests/unit/test_get_news_detail_use_case.py`
- **Test types**: Unit (pytest)
- **BDD Acceptance**:
  ```
  When I run pytest tests/unit/test_get_news_detail_use_case.py
  Then all tests pass with scope validation verified
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T02]

import pytest
from unittest.mock import Mock
from uuid import uuid4

from backend.app.application.use_cases.news.get_news_detail import (
    GetNewsDetailUseCase,
    GetNewsDetailRequest
)
from backend.app.domain.entities.user import User, UserRole
from backend.app.domain.entities.news import News, NewsScope, NewsStatus
from backend.app.domain.exceptions.news import NewsAccessForbiddenException
from backend.app.core.exceptions import NotFoundException


def create_mock_news(scope=NewsScope.GENERAL, status=NewsStatus.PUBLISHED):
    return Mock(
        id=uuid4(),
        scope=scope,
        status=status,
    )


class TestGetNewsDetailUseCase:
    def test_general_article_accessible_by_anonymous(self):
        # Arrange
        article = create_mock_news(scope=NewsScope.GENERAL)
        repository = Mock()
        repository.get_by_id.return_value = article
        
        use_case = GetNewsDetailUseCase(repository)
        request = GetNewsDetailRequest(news_id=article.id, current_user=None)
        
        # Act
        result = use_case.execute(request)
        
        # Assert
        assert result == article

    def test_internal_article_accessible_by_member(self):
        # Arrange
        article = create_mock_news(scope=NewsScope.INTERNAL)
        repository = Mock()
        repository.get_by_id.return_value = article
        member = User(id=uuid4(), role=UserRole.MEMBER)
        
        use_case = GetNewsDetailUseCase(repository)
        request = GetNewsDetailRequest(news_id=article.id, current_user=member)
        
        # Act
        result = use_case.execute(request)
        
        # Assert
        assert result == article

    def test_internal_article_forbidden_for_anonymous(self):
        # Arrange
        article = create_mock_news(scope=NewsScope.INTERNAL)
        repository = Mock()
        repository.get_by_id.return_value = article
        
        use_case = GetNewsDetailUseCase(repository)
        request = GetNewsDetailRequest(news_id=article.id, current_user=None)
        
        # Act & Assert
        with pytest.raises(NewsAccessForbiddenException):
            use_case.execute(request)

    def test_internal_article_forbidden_for_supporter(self):
        # Arrange
        article = create_mock_news(scope=NewsScope.INTERNAL)
        repository = Mock()
        repository.get_by_id.return_value = article
        supporter = User(id=uuid4(), role=UserRole.SUPPORTER)
        
        use_case = GetNewsDetailUseCase(repository)
        request = GetNewsDetailRequest(news_id=article.id, current_user=supporter)
        
        # Act & Assert
        with pytest.raises(NewsAccessForbiddenException):
            use_case.execute(request)

    def test_not_found_for_nonexistent(self):
        # Arrange
        repository = Mock()
        repository.get_by_id.return_value = None
        
        use_case = GetNewsDetailUseCase(repository)
        request = GetNewsDetailRequest(news_id=uuid4(), current_user=None)
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            use_case.execute(request)

    def test_draft_hidden_from_non_admin(self):
        # Arrange
        article = create_mock_news(status=NewsStatus.DRAFT)
        repository = Mock()
        repository.get_by_id.return_value = article
        member = User(id=uuid4(), role=UserRole.MEMBER)
        
        use_case = GetNewsDetailUseCase(repository)
        request = GetNewsDetailRequest(news_id=article.id, current_user=member)
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            use_case.execute(request)

    def test_admin_can_see_draft(self):
        # Arrange
        article = create_mock_news(status=NewsStatus.DRAFT)
        repository = Mock()
        repository.get_by_id.return_value = article
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        
        use_case = GetNewsDetailUseCase(repository)
        request = GetNewsDetailRequest(news_id=article.id, current_user=admin)
        
        # Act
        result = use_case.execute(request)
        
        # Assert
        assert result == article
```

---

### Task 6: Write Integration Tests
- **Purpose**: Verify API with real database.
- **Prerequisites**: Task 4
- **Artifacts impacted**: 
  - `backend/tests/integration/test_news_api.py` (add detail tests)
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  When I run pytest tests/integration/test_news_api.py -k detail
  Then all detail tests pass
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-BE-T02]

def test_get_news_detail_general_anonymous(client, published_general_news):
    """Anonymous can access GENERAL article."""
    response = client.get(f"/api/news/{published_general_news.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(published_general_news.id)
    assert data["content"] is not None  # Full content returned


def test_get_news_detail_internal_member(client, member_auth_headers, published_internal_news):
    """Member can access INTERNAL article."""
    response = client.get(
        f"/api/news/{published_internal_news.id}",
        headers=member_auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["scope"] == "INTERNAL"


def test_get_news_detail_internal_anonymous_forbidden(client, published_internal_news):
    """Anonymous cannot access INTERNAL article."""
    response = client.get(f"/api/news/{published_internal_news.id}")
    
    assert response.status_code == 403
    assert "socios" in response.json()["detail"].lower()


def test_get_news_detail_internal_supporter_forbidden(client, supporter_auth_headers, published_internal_news):
    """Supporter cannot access INTERNAL article."""
    response = client.get(
        f"/api/news/{published_internal_news.id}",
        headers=supporter_auth_headers,
    )
    
    assert response.status_code == 403


def test_get_news_detail_not_found(client):
    """Non-existent article returns 404."""
    from uuid import uuid4
    response = client.get(f"/api/news/{uuid4()}")
    
    assert response.status_code == 404


def test_get_news_detail_deleted_not_found(client, deleted_news):
    """Deleted article returns 404."""
    response = client.get(f"/api/news/{deleted_news.id}")
    
    assert response.status_code == 404


def test_get_news_detail_draft_hidden(client, draft_news):
    """Draft article returns 404 for non-admin."""
    response = client.get(f"/api/news/{draft_news.id}")
    
    assert response.status_code == 404


def test_get_news_detail_draft_visible_to_admin(client, admin_auth_headers, draft_news):
    """Admin can see draft article."""
    response = client.get(
        f"/api/news/{draft_news.id}",
        headers=admin_auth_headers,
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "DRAFT"
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Unit Tests | `docker compose exec backend pytest tests/unit/test_get_news_detail_use_case.py -v` | All pass |
| Integration (API) | `docker compose exec backend pytest tests/integration/test_news_api.py -k detail -v` | All pass |
| All Tests | `docker compose exec backend pytest -v` | All pass |

### Manual Verification
1. Start containers: `docker compose up -d`
2. Open Swagger: `http://localhost:8005/docs`
3. **GENERAL article (anonymous)**:
   - Create and publish GENERAL article
   - GET `/api/news/{id}` without auth
   - Verify 200 with full content
4. **INTERNAL article (member)**:
   - Create and publish INTERNAL article
   - GET with member token
   - Verify 200 with full content
5. **INTERNAL article (anonymous)**:
   - GET same INTERNAL article without auth
   - Verify 403 Forbidden with message "Esta noticia es solo para socios"
6. **Non-existent**:
   - GET with random UUID
   - Verify 404 Not Found

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `backend/app/domain/exceptions/news.py` | CREATE/MODIFY |
| `backend/app/presentation/schemas/news.py` | MODIFY (add NewsDetailResponse) |
| `backend/app/application/use_cases/news/get_news_detail.py` | CREATE |
| `backend/app/application/use_cases/news/__init__.py` | MODIFY |
| `backend/app/presentation/api/news.py` | MODIFY (add GET by ID handler) |
| `backend/tests/unit/test_get_news_detail_use_case.py` | CREATE |
| `backend/tests/integration/test_news_api.py` | MODIFY (add detail tests) |

---

## 7) Access Control Matrix

| Article Scope | Article Status | Anonymous | Supporter | Member | Admin |
|--------------|----------------|-----------|-----------|--------|-------|
| GENERAL | PUBLISHED | ✅ 200 | ✅ 200 | ✅ 200 | ✅ 200 |
| GENERAL | DRAFT | ❌ 404 | ❌ 404 | ❌ 404 | ✅ 200 |
| GENERAL | ARCHIVED | ❌ 404 | ❌ 404 | ❌ 404 | ✅ 200 |
| INTERNAL | PUBLISHED | ❌ 403 | ❌ 403 | ✅ 200 | ✅ 200 |
| INTERNAL | DRAFT | ❌ 404 | ❌ 404 | ❌ 404 | ✅ 200 |
| INTERNAL | ARCHIVED | ❌ 404 | ❌ 404 | ❌ 404 | ✅ 200 |
| ANY | DELETED | ❌ 404 | ❌ 404 | ❌ 404 | ❌ 404 |
