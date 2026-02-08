# NM-MEMBER-001-BE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-MEMBER-001-BE-T01**  
**Related user story**: **NM-MEMBER-001** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All tasks must include inline references to `NM-MEMBER-001-BE-T01`

---

## 1) Context & Objective

### Ticket Summary
Modify GET /api/news to filter based on user role at the database query level. Key requirements:
- **Members/Admins**: See both GENERAL and INTERNAL articles
- **Anonymous/Supporters**: See only GENERAL articles
- **Security Critical**: INTERNAL scope NEVER returned to non-members
- **SQL-level filtering**: No Python-level post-filtering

**Business Value**: Members can access exclusive internal news while protecting member-only content from unauthorized users.

### Impacted Entities/Tables
| Entity | Layer | Operation |
|--------|-------|-----------|
| `ListNewsUseCase` | application/use_cases | MODIFY (role-aware) |
| `NewsRepositoryImpl` | infrastructure/repositories | Already has methods |

### Impacted Services/Modules
| Layer | Module | Operation |
|-------|--------|-----------|
| Application | `list_news.py` | MODIFY (role detection) |
| Infrastructure | `news_repository_impl.py` | VERIFY (scope filtering) |
| Core | `security.py` | VERIFY (user resolution) |

### Impacted BDD Scenarios
This ticket implements:
- **"Member sees all published news"** — Both scopes visible
- **"Supporter sees General only"** — INTERNAL filtered out
- **"Security: INTERNAL never leaked"** — Enforced at SQL level

---

## 2) Scope

### In Scope
- Verify/enhance role-based query filtering in repository
- Update ListNewsUseCase with explicit role handling
- Add optional `scope` filter for admin use
- Unit and integration tests for RBAC
- Security tests to verify no data leakage

### Out of Scope
- Per-article permission caching
- Complex ACL rules
- Frontend changes (covered in FE-T01)

### Assumptions
1. **DB-T01 complete**: News table and scope enum exist
2. **User Management exists**: Role resolution available
3. **Repository methods exist**: `list_public`, `list_for_member` from NM-PUBLIC-001-BE-T01

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Security-First Tests
1. **Security tests (highest priority)**:
   - Test anonymous user NEVER receives INTERNAL articles
   - Test Supporter NEVER receives INTERNAL articles
   - Test Member receives both GENERAL and INTERNAL
   - Test Admin receives all including drafts

2. **Unit tests for ListNewsUseCase**:
   - Test role detection routes to correct repository method
   - Test optional scope filter works for admin

#### Phase 2: GREEN — Minimal Implementation
1. Verify/enhance repository query filtering
2. Update use case with role-based method selection
3. Add optional scope query param for admin
4. Run security tests to verify GREEN

### 3.2 NFR Hooks

#### Security (CRITICAL)
- INTERNAL scope filtered at SQL WHERE clause
- No Python-level filtering after query
- No INTERNAL data in response for non-members
- Test with SQL logging to verify query structure

#### Performance
- Single optimized query per request
- No N+1 queries for permission checks

---

## 4) Atomic Task Breakdown

### Task 1: Verify Repository Scope Filtering
- **Purpose**: Audit existing repository methods for SQL-level filtering.
- **Prerequisites**: NM-PUBLIC-001-BE-T01 complete
- **Artifacts impacted**: 
  - `backend/app/infrastructure/repositories/news_repository_impl.py` (audit)
- **Test types**: Security audit
- **BDD Acceptance**:
  ```
  Given list_public method
  Then SQL includes WHERE scope = 'GENERAL' at query level
  
  Given list_for_member method  
  Then SQL includes all scopes (no scope filter)
  ```

**Audit Checklist**:
```python
# [Feature: News Management] [Story: NM-MEMBER-001] [Ticket: NM-MEMBER-001-BE-T01]

# VERIFY in news_repository_impl.py:

def list_public(...):
    # MUST have this filter:
    .filter(NewsModel.scope == NewsScope.GENERAL)
    # This is the SQL-level enforcement

def list_for_member(...):
    # SHOULD NOT filter by scope (members see all)
    # Only filter by status and is_deleted
```

---

### Task 2: Enhance ListNewsUseCase Role Detection
- **Purpose**: Ensure correct method is called based on role.
- **Prerequisites**: Task 1
- **Artifacts impacted**: 
  - `backend/app/application/use_cases/news/list_news.py`
- **Test types**: Unit
- **BDD Acceptance**:
  ```
  # Scenario: Anonymous user
  Given current_user is None
  When I execute ListNewsUseCase
  Then list_public is called (GENERAL only)
  
  # Scenario: Supporter
  Given current_user.role = SUPPORTER
  When I execute ListNewsUseCase
  Then list_public is called (GENERAL only)
  
  # Scenario: Member
  Given current_user.role = MEMBER
  When I execute ListNewsUseCase
  Then list_for_member is called (all scopes)
  
  # Scenario: Admin
  Given current_user.role = ADMIN
  When I execute ListNewsUseCase
  Then list_all is called (all statuses)
  ```

**Use Case Template**:
```python
# [Feature: News Management] [Story: NM-MEMBER-001] [Ticket: NM-MEMBER-001-BE-T01]

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

from backend.app.domain.repositories.news_repository import NewsRepository
from backend.app.domain.entities.user import User, UserRole
from backend.app.domain.entities.news import News, NewsScope


@dataclass
class ListNewsRequest:
    skip: int = 0
    limit: int = 20
    search: Optional[str] = None
    scope: Optional[NewsScope] = None  # Admin-only filter
    current_user: Optional[User] = None


class ListNewsUseCase:
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def execute(self, request: ListNewsRequest):
        limit = min(request.limit, 100)
        user = request.current_user
        
        # Determine access level based on role
        if user and user.role == UserRole.ADMIN:
            # Admin sees everything (all statuses, all scopes)
            # Optionally filter by scope if requested
            items, total = self.repository.list_all(
                skip=request.skip,
                limit=limit,
                search=request.search,
                scope=request.scope,  # Admin can filter by scope
            )
        elif user and user.role == UserRole.MEMBER:
            # Member sees all published articles (both scopes)
            items, total = self.repository.list_for_member(
                skip=request.skip,
                limit=limit,
                search=request.search,
            )
        else:
            # Anonymous, Supporter, etc: GENERAL scope only
            # SECURITY: This is enforced at SQL level in list_public
            items, total = self.repository.list_public(
                skip=request.skip,
                limit=limit,
                search=request.search,
            )
        
        return ListNewsResponse(
            items=items,
            total=total,
            skip=request.skip,
            limit=limit,
        )
```

---

### Task 3: Add Optional Scope Filter for Admin
- **Purpose**: Allow admin to filter by scope for management views.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `backend/app/infrastructure/repositories/news_repository_impl.py`
  - `backend/app/presentation/api/news.py`
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  # Scenario: Admin filters by scope
  Given admin user
  When GET /api/news?scope=INTERNAL
  Then only INTERNAL articles are returned
  
  # Scenario: Non-admin cannot use scope filter
  Given member user
  When GET /api/news?scope=INTERNAL
  Then scope parameter is ignored
  ```

**Endpoint Update**:
```python
# [Feature: News Management] [Story: NM-MEMBER-001] [Ticket: NM-MEMBER-001-BE-T01]

from backend.app.domain.entities.news import NewsScope

@router.get("", response_model=PaginatedNewsResponse)
def list_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    scope: Optional[NewsScope] = Query(None, description="Admin only: filter by scope"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    # scope filter only applied for admins
    applied_scope = scope if (current_user and current_user.role == UserRole.ADMIN) else None
    
    request = ListNewsRequest(
        skip=skip,
        limit=limit,
        search=search,
        scope=applied_scope,
        current_user=current_user,
    )
    # ... rest of handler
```

---

### Task 4: Write Security Tests
- **Purpose**: Critical tests to verify no data leakage.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `backend/tests/security/test_news_scope_access.py`
- **Test types**: Security (pytest)
- **BDD Acceptance**:
  ```
  When I run pytest tests/security/test_news_scope_access.py
  Then all security assertions pass
  ```

**Security Test Template**:
```python
# [Feature: News Management] [Story: NM-MEMBER-001] [Ticket: NM-MEMBER-001-BE-T01]

"""
SECURITY TESTS: News Scope Access Control

These tests verify that INTERNAL articles are NEVER returned to 
non-member users. This is a critical RBAC boundary.
"""

import pytest


class TestNewsScopeSecurityBoundary:
    """Critical security tests for INTERNAL scope protection."""

    def test_anonymous_never_sees_internal_articles(self, client, internal_article):
        """
        SECURITY: Anonymous users must NEVER see INTERNAL articles.
        
        This is enforced at SQL level in list_public() method.
        """
        response = client.get("/api/news")
        
        assert response.status_code == 200
        items = response.json()["items"]
        
        # CRITICAL ASSERTION: No INTERNAL articles
        for item in items:
            assert item["scope"] != "INTERNAL", \
                f"SECURITY VIOLATION: INTERNAL article {item['id']} leaked to anonymous user!"

    def test_supporter_never_sees_internal_articles(self, client, supporter_auth_headers, internal_article):
        """
        SECURITY: Supporter role must NEVER see INTERNAL articles.
        
        Supporters are not association members.
        """
        response = client.get("/api/news", headers=supporter_auth_headers)
        
        assert response.status_code == 200
        items = response.json()["items"]
        
        # CRITICAL ASSERTION: No INTERNAL articles
        for item in items:
            assert item["scope"] != "INTERNAL", \
                f"SECURITY VIOLATION: INTERNAL article {item['id']} leaked to supporter!"

    def test_member_sees_internal_articles(self, client, member_auth_headers, internal_article):
        """
        Member users CAN see INTERNAL articles.
        """
        response = client.get("/api/news", headers=member_auth_headers)
        
        assert response.status_code == 200
        items = response.json()["items"]
        
        # Members should see INTERNAL articles
        internal_ids = [item["id"] for item in items if item["scope"] == "INTERNAL"]
        assert len(internal_ids) > 0, "Member should see INTERNAL articles"

    def test_admin_sees_internal_articles(self, client, admin_auth_headers, internal_article):
        """
        Admin users CAN see INTERNAL articles.
        """
        response = client.get("/api/news", headers=admin_auth_headers)
        
        assert response.status_code == 200
        items = response.json()["items"]
        
        internal_ids = [item["id"] for item in items if item["scope"] == "INTERNAL"]
        assert len(internal_ids) > 0, "Admin should see INTERNAL articles"


class TestScopeFilterNotExploitable:
    """Ensure scope filter cannot be exploited by non-admins."""

    def test_anonymous_cannot_bypass_with_scope_param(self, client, internal_article):
        """
        SECURITY: Anonymous cannot access INTERNAL by passing scope param.
        """
        response = client.get("/api/news", params={"scope": "INTERNAL"})
        
        assert response.status_code == 200
        items = response.json()["items"]
        
        # Scope param should be ignored for anonymous
        for item in items:
            assert item["scope"] != "INTERNAL", \
                "SECURITY VIOLATION: scope param bypass!"

    def test_supporter_cannot_bypass_with_scope_param(self, client, supporter_auth_headers, internal_article):
        """
        SECURITY: Supporter cannot access INTERNAL by passing scope param.
        """
        response = client.get(
            "/api/news", 
            params={"scope": "INTERNAL"},
            headers=supporter_auth_headers,
        )
        
        assert response.status_code == 200
        items = response.json()["items"]
        
        for item in items:
            assert item["scope"] != "INTERNAL", \
                "SECURITY VIOLATION: scope param bypass by supporter!"
```

---

### Task 5: Write Unit Tests
- **Purpose**: TDD validation for role-based routing.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `backend/tests/unit/test_list_news_use_case.py`
- **Test types**: Unit (pytest)
- **BDD Acceptance**:
  ```
  When I run pytest tests/unit/test_list_news_use_case.py -k role
  Then all role-based tests pass
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-MEMBER-001] [Ticket: NM-MEMBER-001-BE-T01]

import pytest
from unittest.mock import Mock
from uuid import uuid4

from backend.app.application.use_cases.news.list_news import (
    ListNewsUseCase,
    ListNewsRequest,
)
from backend.app.domain.entities.user import User, UserRole


class TestListNewsUseCaseRoleBasedAccess:
    """Test that correct repository method is called based on user role."""

    def test_anonymous_calls_list_public(self):
        """Anonymous users get list_public (GENERAL only)."""
        repository = Mock()
        repository.list_public.return_value = ([], 0)
        
        use_case = ListNewsUseCase(repository)
        request = ListNewsRequest(current_user=None)
        
        use_case.execute(request)
        
        repository.list_public.assert_called_once()
        repository.list_for_member.assert_not_called()
        repository.list_all.assert_not_called()

    def test_supporter_calls_list_public(self):
        """Supporter users get list_public (GENERAL only)."""
        repository = Mock()
        repository.list_public.return_value = ([], 0)
        supporter = User(id=uuid4(), role=UserRole.SUPPORTER)
        
        use_case = ListNewsUseCase(repository)
        request = ListNewsRequest(current_user=supporter)
        
        use_case.execute(request)
        
        repository.list_public.assert_called_once()
        repository.list_for_member.assert_not_called()

    def test_member_calls_list_for_member(self):
        """Member users get list_for_member (all scopes)."""
        repository = Mock()
        repository.list_for_member.return_value = ([], 0)
        member = User(id=uuid4(), role=UserRole.MEMBER)
        
        use_case = ListNewsUseCase(repository)
        request = ListNewsRequest(current_user=member)
        
        use_case.execute(request)
        
        repository.list_for_member.assert_called_once()
        repository.list_public.assert_not_called()

    def test_admin_calls_list_all(self):
        """Admin users get list_all (all statuses and scopes)."""
        repository = Mock()
        repository.list_all.return_value = ([], 0)
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        
        use_case = ListNewsUseCase(repository)
        request = ListNewsRequest(current_user=admin)
        
        use_case.execute(request)
        
        repository.list_all.assert_called_once()
        repository.list_for_member.assert_not_called()
        repository.list_public.assert_not_called()
```

---

### Task 6: Write Integration Tests
- **Purpose**: End-to-end verification with real database.
- **Prerequisites**: Task 4
- **Artifacts impacted**: 
  - `backend/tests/integration/test_news_api.py`
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  When I run pytest tests/integration/test_news_api.py -k scope
  Then all scope tests pass
  ```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Security Tests | `docker compose exec backend pytest tests/security/test_news_scope_access.py -v` | All pass |
| Unit Tests | `docker compose exec backend pytest tests/unit/test_list_news_use_case.py -k role -v` | All pass |
| Integration | `docker compose exec backend pytest tests/integration/test_news_api.py -k scope -v` | All pass |
| All Backend | `docker compose exec backend pytest -v` | All pass |

### Manual Verification
1. Start containers: `docker compose up -d`
2. Open Swagger: `http://localhost:8005/docs`
3. **Anonymous test**:
   - GET `/api/news` without auth
   - Verify NO articles have scope="INTERNAL"
4. **Supporter test**:
   - Login as supporter
   - GET `/api/news`
   - Verify NO articles have scope="INTERNAL"
5. **Member test**:
   - Login as member
   - GET `/api/news`
   - Verify INTERNAL articles ARE visible
6. **Admin scope filter**:
   - Login as admin
   - GET `/api/news?scope=INTERNAL`
   - Verify only INTERNAL articles returned

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `backend/app/application/use_cases/news/list_news.py` | MODIFY (role detection) |
| `backend/app/presentation/api/news.py` | MODIFY (scope param for admin) |
| `backend/tests/security/test_news_scope_access.py` | CREATE |
| `backend/tests/unit/test_list_news_use_case.py` | MODIFY (role tests) |
| `backend/tests/integration/test_news_api.py` | MODIFY (scope tests) |

---

## 7) Security Compliance Checklist

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| INTERNAL filtered at SQL | ✅ | `list_public` has `.filter(scope == GENERAL)` |
| No Python post-filtering | ✅ | WHERE clause in query, not list comprehension |
| Anonymous can't see INTERNAL | ✅ | Routes to `list_public` |
| Supporter can't see INTERNAL | ✅ | Routes to `list_public` |
| Member sees INTERNAL | ✅ | Routes to `list_for_member` |
| Admin scope param | ✅ | Only applied if role == ADMIN |
| No scope bypass | ✅ | Non-admin scope param ignored |

---

## 8) Role Access Matrix

| Role | GENERAL Published | INTERNAL Published | Draft/Archived |
|------|-------------------|-------------------|----------------|
| Anonymous | ✅ | ❌ | ❌ |
| Supporter | ✅ | ❌ | ❌ |
| Member | ✅ | ✅ | ❌ |
| Admin | ✅ | ✅ | ✅ |
