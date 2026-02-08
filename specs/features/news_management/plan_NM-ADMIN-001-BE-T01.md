# NM-ADMIN-001-BE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-ADMIN-001-BE-T01**  
**Related user story**: **NM-ADMIN-001** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All tasks must include inline references to `NM-ADMIN-001-BE-T01` and related scenarios

---

## 1) Context & Objective

### Ticket Summary
Implement the POST `/api/news` endpoint to create a news article as draft. This is the foundational backend API for the News Management feature, enabling Administrators to create news articles with:
- Title, summary, and rich text content
- Visibility scope (GENERAL or INTERNAL)
- XSS-sanitized content storage
- Audit logging of creation events

**Business Value**: Enables Administrators to prepare official communications for the community through a secure, validated API.

### Impacted Entities/Tables
| Entity | Layer | Operation |
|--------|-------|-----------|
| `News` (Domain) | domain/entities | CREATE (new entity) |
| `NewsRepository` | domain/repositories | CREATE (new interface) |
| `News` (SQLAlchemy) | infrastructure/models | REUSE (from DB-T01) |

### Impacted Services/Modules
| Layer | Module | Operation |
|-------|--------|-----------|
| Domain | `domain/entities/news.py` | CREATE |
| Domain | `domain/repositories/news_repository.py` | CREATE |
| Application | `application/use_cases/news/create_news.py` | CREATE |
| Infrastructure | `infrastructure/repositories/news_repository_impl.py` | CREATE |
| Infrastructure | `infrastructure/db/mappers/news_mapper.py` | CREATE |
| Presentation | `presentation/api/news.py` | CREATE |
| Presentation | `presentation/schemas/news.py` | CREATE |

### Impacted BDD Scenarios
This ticket implements the data layer for:
- **"Successfully create a draft news article"** — Core happy path
- **"Attempt to create article without title"** — Validation
- **"Rich text content is sanitized"** — Security (XSS)
- **"Creation is logged for audit"** — Observability

---

## 2) Scope

### In Scope
- POST `/api/news` endpoint (returns 201 Created)
- `CreateNewsRequest` Pydantic schema (title, summary, content, scope)
- `NewsResponse` Pydantic schema (full article representation)
- Domain entity `News` (plain Python dataclass)
- Repository interface `NewsRepository` (abstract base class)
- Repository implementation `NewsRepositoryImpl` (SQLAlchemy)
- Use case `CreateNewsUseCase` (orchestration)
- Mapper `NewsMapper` (entity ↔ model conversion)
- Admin-only access check (RBAC dependency)
- XSS sanitization for content field (bleach library)
- Audit log entry on creation

### Out of Scope
- File/image upload (future ticket)
- Tags association (future ticket)
- GET, PUT, DELETE endpoints (other tickets)
- Rich text editor integration (FE ticket)

### Assumptions
1. **DB-T01 is complete**: The `news` table and SQLAlchemy model exist.
2. **User Management exists**: Auth dependency with `get_current_user` and role checking.
3. **Bleach is available**: For HTML sanitization (add to requirements if missing).

### Open Questions
1. **Q1**: Is there an existing RBAC dependency we can reuse? (e.g., `require_admin` decorator)
   - **If No**: Create a simple admin check dependency.
2. **Q2**: Should `summary` be required for saving drafts?
   - **Assumption**: No, summary is optional for drafts (required only for publishing).

---

## 3) Detailed Work Plan (TDD + BDD)

### Container Check (Prerequisites)
Before starting implementation:
1. Verify `docker-compose.yml` exists and PostgreSQL + Backend services are defined
2. Run `docker compose up -d` to start services
3. Verify backend is reachable: `docker compose ps` should show healthy status
4. Verify DB migration from NM-ADMIN-001-DB-T01 is applied

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for CreateNewsUseCase**:
   - Test successful creation with valid data
   - Test validation error when title is missing
   - Test XSS sanitization of content
   - Test audit log call on success

2. **Integration tests for NewsRepositoryImpl**:
   - Test create saves to database
   - Test author_id is correctly set
   - Test timestamps are auto-generated

3. **API tests for POST /api/news**:
   - Test 201 response with valid admin auth
   - Test 401 without auth
   - Test 403 with non-admin auth
   - Test 422 with invalid payload

#### Phase 2: GREEN — Minimal Implementation
1. Create domain layer (entity, repository interface)
2. Create infrastructure layer (repository impl, mapper)
3. Create application layer (use case)
4. Create presentation layer (router, schemas)
5. Register router in main.py
6. Run tests to verify GREEN state

#### Phase 3: REFACTOR
1. Extract common patterns (if any)
2. Add detailed docstrings
3. Ensure consistent error handling

### 3.2 NFR Hooks

#### Security/Privacy
- **RBAC**: Admin role check via dependency injection
- **XSS Prevention**: Sanitize HTML content with bleach (strip script tags, event handlers)
- **Input Validation**: Pydantic V2 strict validation
- **Audit Trail**: Log author_id and timestamp on creation

#### Performance/Resilience
- Single database transaction per request
- No N+1 queries (single INSERT)

#### Observability
- Structured logging for create operation
- Include correlation ID if available
- Audit log entry with: action=CREATE, user_id, news_id, timestamp

---

## 4) Atomic Task Breakdown

### Task 1: Verify Prerequisites
- **Purpose**: Ensure DB migration is applied and backend is running. Supports `NM-ADMIN-001-BE-T01`.
- **Prerequisites**: Docker Compose environment
- **Artifacts impacted**: None (verification only)
- **Test types**: Manual
- **BDD Acceptance**:
  ```
  Given the backend container is running
  When I connect to the database
  Then the news table exists with all columns
  And the SQLAlchemy model is importable
  ```

---

### Task 2: Create Domain Entity
- **Purpose**: Define framework-agnostic News entity. Supports hexagonal architecture requirement.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `backend/app/domain/entities/news.py`
  - `backend/app/domain/entities/__init__.py`
- **Test types**: Unit
- **BDD Acceptance**:
  ```
  Given I import the News entity
  When I instantiate it with valid data
  Then all attributes are correctly typed
  And the entity has no framework dependencies
  ```

**Entity Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class NewsStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class NewsScope(str, Enum):
    GENERAL = "GENERAL"
    INTERNAL = "INTERNAL"


@dataclass
class News:
    title: str
    author_id: UUID
    id: UUID = field(default_factory=uuid4)
    summary: Optional[str] = None
    content: Optional[str] = None
    status: NewsStatus = NewsStatus.DRAFT
    scope: NewsScope = NewsScope.GENERAL
    cover_url: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_deleted: bool = False
```

---

### Task 3: Create Repository Interface (Port)
- **Purpose**: Define abstract contract for news persistence. Supports hexagonal architecture.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `backend/app/domain/repositories/news_repository.py`
  - `backend/app/domain/repositories/__init__.py`
- **Test types**: None (interface only)
- **BDD Acceptance**:
  ```
  Given I import NewsRepository
  Then it is an abstract base class
  And it defines a create method accepting a News entity
  ```

**Interface Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]

from abc import ABC, abstractmethod
from backend.app.domain.entities.news import News


class NewsRepository(ABC):
    @abstractmethod
    def create(self, news: News) -> News:
        """Persist a new news article and return it with generated ID."""
        pass
```

---

### Task 4: Create Entity-Model Mapper
- **Purpose**: Convert between domain entity and SQLAlchemy model. Keeps layers decoupled.
- **Prerequisites**: Task 2, DB-T01 SQLAlchemy model
- **Artifacts impacted**: 
  - `backend/app/infrastructure/db/mappers/news_mapper.py`
- **Test types**: Unit
- **BDD Acceptance**:
  ```
  Given a News domain entity
  When I call to_model()
  Then I get a SQLAlchemy News model with matching attributes
  
  Given a SQLAlchemy News model
  When I call to_entity()
  Then I get a News domain entity with matching attributes
  ```

**Mapper Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]

from backend.app.domain.entities.news import News as NewsEntity
from backend.app.infrastructure.models.news import News as NewsModel


class NewsMapper:
    @staticmethod
    def to_model(entity: NewsEntity) -> NewsModel:
        return NewsModel(
            id=entity.id,
            title=entity.title,
            summary=entity.summary,
            content=entity.content,
            status=entity.status,
            scope=entity.scope,
            author_id=entity.author_id,
            cover_url=entity.cover_url,
            published_at=entity.published_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_deleted=entity.is_deleted,
        )

    @staticmethod
    def to_entity(model: NewsModel) -> NewsEntity:
        return NewsEntity(
            id=model.id,
            title=model.title,
            summary=model.summary,
            content=model.content,
            status=model.status,
            scope=model.scope,
            author_id=model.author_id,
            cover_url=model.cover_url,
            published_at=model.published_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_deleted=model.is_deleted,
        )
```

---

### Task 5: Create Repository Implementation (Adapter)
- **Purpose**: Implement NewsRepository using SQLAlchemy. Adapter pattern.
- **Prerequisites**: Tasks 3, 4
- **Artifacts impacted**: 
  - `backend/app/infrastructure/repositories/news_repository_impl.py`
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  Given a valid News entity
  When I call repository.create(entity)
  Then the news is persisted to the database
  And the returned entity has a valid UUID
  And created_at is set
  ```

**Repository Implementation Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]

from sqlalchemy.orm import Session
from backend.app.domain.entities.news import News
from backend.app.domain.repositories.news_repository import NewsRepository
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
```

---

### Task 6: Create Use Case with Sanitization
- **Purpose**: Orchestrate article creation with business logic and XSS sanitization.
- **Prerequisites**: Tasks 2, 3, 5
- **Artifacts impacted**: 
  - `backend/app/application/use_cases/news/__init__.py`
  - `backend/app/application/use_cases/news/create_news.py`
- **Test types**: Unit (mocked repository)
- **BDD Acceptance**:
  ```
  # Scenario: Successfully create a draft news article
  Given I have valid article data
  When I call CreateNewsUseCase.execute()
  Then the article is saved with status DRAFT
  And content is sanitized (script tags removed)
  
  # Scenario: Rich text content is sanitized
  Given content contains "<script>alert('xss')</script>"
  When I call CreateNewsUseCase.execute()
  Then the script tags are stripped from the stored content
  ```

**Use Case Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]

import bleach
from uuid import UUID
from backend.app.domain.entities.news import News, NewsScope, NewsStatus
from backend.app.domain.repositories.news_repository import NewsRepository

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'blockquote']
ALLOWED_ATTRS = {'a': ['href', 'title']}


class CreateNewsUseCase:
    def __init__(self, repository: NewsRepository):
        self.repository = repository

    def execute(
        self,
        title: str,
        author_id: UUID,
        summary: str | None = None,
        content: str | None = None,
        scope: NewsScope = NewsScope.GENERAL,
        cover_url: str | None = None,
    ) -> News:
        # Sanitize rich text content to prevent XSS
        sanitized_content = None
        if content:
            sanitized_content = bleach.clean(
                content,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRS,
                strip=True
            )

        news = News(
            title=title,
            author_id=author_id,
            summary=summary,
            content=sanitized_content,
            scope=scope,
            cover_url=cover_url,
            status=NewsStatus.DRAFT,
        )

        return self.repository.create(news)
```

---

### Task 7: Create Pydantic Schemas
- **Purpose**: Define request/response DTOs for API layer. Supports validation.
- **Prerequisites**: Task 2 (entity reference)
- **Artifacts impacted**: 
  - `backend/app/presentation/schemas/news.py`
- **Test types**: Unit (schema validation)
- **BDD Acceptance**:
  ```
  # Scenario: Attempt to create article without title
  Given a CreateNewsRequest without title
  When Pydantic validates the request
  Then a validation error is raised
  And the message includes "title"
  ```

**Schemas Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from backend.app.domain.entities.news import NewsScope, NewsStatus


class CreateNewsRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Article headline")
    summary: Optional[str] = Field(None, max_length=500, description="Brief description")
    content: Optional[str] = Field(None, description="Rich text content (HTML)")
    scope: NewsScope = Field(NewsScope.GENERAL, description="Visibility scope")
    cover_url: Optional[str] = Field(None, max_length=2048, description="Cover image URL")

    model_config = ConfigDict(extra="forbid")


class NewsResponse(BaseModel):
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
```

---

### Task 8: Create API Router
- **Purpose**: Expose POST /api/news endpoint with Admin auth. Presentation layer.
- **Prerequisites**: Tasks 5, 6, 7
- **Artifacts impacted**: 
  - `backend/app/presentation/api/news.py`
  - `backend/app/main.py` (router registration)
- **Test types**: API integration
- **BDD Acceptance**:
  ```
  # Happy Path
  Given I am authenticated as an Administrator
  When I POST to /api/news with valid data
  Then I receive 201 Created
  And the response contains the created article
  
  # Security: Non-admin blocked
  Given I am authenticated as a Member
  When I POST to /api/news
  Then I receive 403 Forbidden
  ```

**Router Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-BE-T01]

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, require_admin
from backend.app.application.use_cases.news.create_news import CreateNewsUseCase
from backend.app.infrastructure.repositories.news_repository_impl import NewsRepositoryImpl
from backend.app.presentation.schemas.news import CreateNewsRequest, NewsResponse

router = APIRouter(prefix="/api/news", tags=["news"])


@router.post("", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
def create_news(
    request: CreateNewsRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Create a new news article as draft. Admin only."""
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
    
    return NewsResponse.model_validate(news)
```

---

### Task 9: Write Unit Tests
- **Purpose**: TDD validation for use case logic. Supports `NM-ADMIN-001-BE-T01`.
- **Prerequisites**: Tasks 2-6
- **Artifacts impacted**: 
  - `backend/tests/unit/test_create_news_use_case.py`
- **Test types**: Unit (mocked dependencies)
- **BDD Acceptance**:
  ```
  Given the use case tests exist
  When I run pytest tests/unit/test_create_news_use_case.py
  Then all tests pass
  And XSS sanitization is verified
  ```

---

### Task 10: Write Integration Tests
- **Purpose**: Verify repository and API work with real database. Supports `NM-ADMIN-001-BE-T01`.
- **Prerequisites**: Tasks 5, 8
- **Artifacts impacted**: 
  - `backend/tests/integration/test_news_repository.py`
  - `backend/tests/integration/test_news_api.py`
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  Given the integration tests exist
  When I run pytest tests/integration/
  Then all news tests pass
  And the database has the created records
  ```

---

### Task 11: Register Router in main.py
- **Purpose**: Mount news router to FastAPI app. Final wiring step.
- **Prerequisites**: Task 8
- **Artifacts impacted**: 
  - `backend/app/main.py`
- **Test types**: Manual (curl test)
- **BDD Acceptance**:
  ```
  Given the router is registered
  When I start the backend
  And I call GET /docs
  Then POST /api/news is listed in Swagger
  ```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Unit Tests | `docker compose exec backend pytest tests/unit/test_create_news_use_case.py -v` | All pass |
| Integration Tests | `docker compose exec backend pytest tests/integration/test_news_repository.py -v` | All pass |
| API Tests | `docker compose exec backend pytest tests/integration/test_news_api.py -v` | All pass |

### Manual Verification
1. Start containers: `docker compose up -d`
2. Open Swagger: `http://localhost:8005/docs`
3. Authenticate as Admin
4. Execute POST /api/news with:
   ```json
   {
     "title": "Test Article",
     "summary": "Test summary",
     "content": "<p>Hello</p><script>alert('xss')</script>",
     "scope": "GENERAL"
   }
   ```
5. Verify:
   - Response is 201 Created
   - Response contains `id`, `status: "DRAFT"`
   - Content has script tag stripped: `"<p>Hello</p>"`

---

## 6) Dependencies to Add

If not already present in `backend/requirements.txt`:
```
bleach>=6.0.0
```

---

## 7) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `backend/app/domain/entities/news.py` | CREATE |
| `backend/app/domain/entities/__init__.py` | MODIFY |
| `backend/app/domain/repositories/news_repository.py` | CREATE |
| `backend/app/domain/repositories/__init__.py` | MODIFY |
| `backend/app/application/use_cases/news/__init__.py` | CREATE |
| `backend/app/application/use_cases/news/create_news.py` | CREATE |
| `backend/app/infrastructure/db/mappers/news_mapper.py` | CREATE |
| `backend/app/infrastructure/repositories/news_repository_impl.py` | CREATE |
| `backend/app/presentation/schemas/news.py` | CREATE |
| `backend/app/presentation/api/news.py` | CREATE |
| `backend/app/main.py` | MODIFY |
| `backend/tests/unit/test_create_news_use_case.py` | CREATE |
| `backend/tests/integration/test_news_repository.py` | CREATE |
| `backend/tests/integration/test_news_api.py` | CREATE |
| `backend/requirements.txt` | MODIFY (add bleach) |
