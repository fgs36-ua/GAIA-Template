# NM-ADMIN-001-DB-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-ADMIN-001-DB-T01**  
**Related user story**: **NM-ADMIN-001** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All tasks must include inline references to `NM-ADMIN-001-DB-T01` and scenario "Successfully create a draft news article"

---

## 1) Context & Objective

### Ticket Summary
Create the foundational database schema for the News Management feature. This includes:
- The `news` table with all required fields for article storage
- Two PostgreSQL ENUMs (`news_status`, `news_scope`) for type-safe status and visibility management
- Foreign key relationship to the `users` table for author tracking
- Soft delete support via `is_deleted` boolean flag

**Business Value**: Enables all downstream tickets (BE and FE) to persist and retrieve news articles. Essential foundation for the entire News Management feature.

### Impacted Entities/Tables
| Entity | Operation |
|--------|-----------|
| `news` | CREATE (new table) |
| `news_status` | CREATE (new enum) |
| `news_scope` | CREATE (new enum) |

### Impacted Services/Modules
- `infrastructure/models/news.py` — SQLAlchemy model
- `backend/alembic/versions/` — New migration script
- `specs/DataModel.md` — Documentation update

### Impacted BDD Scenarios
This ticket enables the data layer for:
- **NM-ADMIN-001**: "Successfully create a draft news article" (storage)
- **NM-ADMIN-001**: "Creation is logged for audit" (author_id tracking)
- **NM-MEMBER-001**: "API-level filtering" (scope column for RBAC queries)

---

## 2) Scope

### In Scope
- `news` table with columns: `id`, `title`, `summary`, `content`, `status`, `scope`, `author_id`, `cover_url`, `published_at`, `created_at`, `updated_at`, `is_deleted`
- `news_status` enum: `DRAFT`, `PUBLISHED`, `ARCHIVED`
- `news_scope` enum: `GENERAL`, `INTERNAL`
- Foreign key constraint: `author_id` → `users.id`
- Indexes: `status`, `scope`, `is_deleted`, `published_at` (for common query patterns)
- Alembic migration (reversible)
- SQLAlchemy model

### Out of Scope
- Tags table (future ticket)
- Attachments table (future ticket)
- Full-text search indexes (future ticket NM-PUBLIC-002)
- Audit log table (handled by observability infrastructure)

### Assumptions
1. **User Management exists**: A `users` table with `id` (UUID) column exists for the FK relationship.
2. **PostgreSQL 14+**: ENUM types are supported.
3. **Alembic is configured**: Migration infrastructure is already set up in `backend/alembic/`.

### Open Questions
1. **Q1**: Does the `users` table exist? If not, this ticket is blocked.
   - **Resolution**: Check if `backend/app/infrastructure/models/user.py` exists. If not, create a stub or defer to User Management feature.

---

## 3) Detailed Work Plan (TDD + BDD)

### Container Check (Prerequisites)
Before starting implementation:
1. Verify `docker-compose.yml` exists in project root
2. Run `docker compose up -d` to start PostgreSQL
3. Verify database is reachable: `docker compose ps` should show healthy status
4. If containers are not healthy, **STOP** and resolve infrastructure issues first

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. Create integration test for migration:
   - Test that migration applies successfully (`alembic upgrade head`)
   - Test that migration can be rolled back (`alembic downgrade -1`)
   - Test that table `news` exists with expected columns
   - Test that enums `news_status` and `news_scope` exist

2. Create unit test for SQLAlchemy model:
   - Test model instantiation with valid data
   - Test enum value constraints
   - Test relationship to User model (if available)

#### Phase 2: GREEN — Minimal Implementation
1. Create Alembic migration script
2. Create SQLAlchemy model
3. Run tests to verify GREEN state

#### Phase 3: REFACTOR
1. Add documentation to model
2. Ensure naming conventions are consistent
3. Update `specs/DataModel.md`

### 3.2 NFR Hooks

#### Security/Privacy
- `author_id` FK ensures data integrity and enables audit trails
- No PII stored directly in news table (author referenced by FK only)
- `is_deleted` soft delete preserves audit history

#### Performance
- Indexes on frequently queried columns: `status`, `scope`, `is_deleted`, `published_at`
- Composite index consideration: `(is_deleted, status, scope)` for list queries

#### Observability
- `created_at`, `updated_at` timestamps for audit purposes
- `author_id` enables tracking of who created/modified articles

---

## 4) Atomic Task Breakdown

### Task 1: Verify Prerequisites
- **Purpose**: Ensure database infrastructure is ready before creating migration. Supports `NM-ADMIN-001-DB-T01`.
- **Prerequisites**: Docker Compose environment with PostgreSQL
- **Artifacts impacted**: None (verification only)
- **Test types**: Manual verification
- **BDD Acceptance**:
  ```
  Given the project has a docker-compose.yml
  When I run `docker compose up -d`
  And I run `docker compose ps`
  Then I see the database container in "healthy" or "running" state
  ```

---

### Task 2: Check User Table Dependency
- **Purpose**: Verify `users` table exists for FK constraint. Supports `NM-ADMIN-001-DB-T01` dependency.
- **Prerequisites**: Database running
- **Artifacts impacted**: None (verification only) or create stub if missing
- **Test types**: Manual verification
- **BDD Acceptance**:
  ```
  Given I connect to the PostgreSQL database
  When I query for the users table
  Then the table exists with an id column of type UUID
  OR I document that User Management must be implemented first
  ```

---

### Task 3: Create Alembic Migration Script
- **Purpose**: Define database schema for `news` table and enums. Core deliverable for `NM-ADMIN-001-DB-T01`.
- **Prerequisites**: Alembic configured, database running
- **Artifacts impacted**: 
  - `backend/alembic/versions/YYYYMMDD_HHMMSS_create_news_table.py`
- **Test types**: Integration (migration up/down)
- **BDD Acceptance**:
  ```
  Given Alembic is configured
  When I run `alembic revision --autogenerate -m "create_news_table"`
  And I edit the migration to include enums and table definition
  And I run `alembic upgrade head`
  Then the news table is created with all columns
  And the news_status enum contains DRAFT, PUBLISHED, ARCHIVED
  And the news_scope enum contains GENERAL, INTERNAL
  
  When I run `alembic downgrade -1`
  Then the news table is dropped
  And the enums are dropped
  ```

**Migration Script Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-DB-T01]

def upgrade():
    # Create enums
    news_status = sa.Enum('DRAFT', 'PUBLISHED', 'ARCHIVED', name='news_status')
    news_scope = sa.Enum('GENERAL', 'INTERNAL', name='news_scope')
    news_status.create(op.get_bind())
    news_scope.create(op.get_bind())
    
    # Create news table
    op.create_table(
        'news',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('summary', sa.String(500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('status', news_status, nullable=False, default='DRAFT'),
        sa.Column('scope', news_scope, nullable=False, default='GENERAL'),
        sa.Column('author_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('cover_url', sa.String(2048), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_news_status', 'news', ['status'])
    op.create_index('ix_news_scope', 'news', ['scope'])
    op.create_index('ix_news_is_deleted', 'news', ['is_deleted'])
    op.create_index('ix_news_published_at', 'news', ['published_at'])

def downgrade():
    op.drop_table('news')
    sa.Enum(name='news_status').drop(op.get_bind())
    sa.Enum(name='news_scope').drop(op.get_bind())
```

---

### Task 4: Create SQLAlchemy Model
- **Purpose**: Define Python model for ORM operations. Supports `NM-ADMIN-001-DB-T01` deliverable.
- **Prerequisites**: Migration applied
- **Artifacts impacted**: 
  - `backend/app/infrastructure/models/news.py`
  - `backend/app/infrastructure/models/__init__.py` (register model)
- **Test types**: Unit (model instantiation)
- **BDD Acceptance**:
  ```
  Given the migration is applied
  When I create a News model instance with valid data
  Then all fields are properly typed
  And the relationship to User is defined
  And enum fields accept only valid values
  ```

**Model Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-DB-T01]

import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.infrastructure.db.base import Base


class NewsStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class NewsScope(str, enum.Enum):
    GENERAL = "GENERAL"
    INTERNAL = "INTERNAL"


class News(Base):
    __tablename__ = "news"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    summary = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    status = Column(Enum(NewsStatus), nullable=False, default=NewsStatus.DRAFT)
    scope = Column(Enum(NewsScope), nullable=False, default=NewsScope.GENERAL)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cover_url = Column(String(2048), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Relationships
    author = relationship("User", back_populates="news_articles")
```

---

### Task 5: Write Integration Tests
- **Purpose**: Verify migration and model work correctly. TDD validation for `NM-ADMIN-001-DB-T01`.
- **Prerequisites**: Test database configured
- **Artifacts impacted**: 
  - `backend/tests/integration/test_news_model.py`
- **Test types**: Integration
- **BDD Acceptance**:
  ```
  Given the test database is running
  When I run the news model integration tests
  Then all tests pass
  And I can create, read, update a News record
  And soft delete works (is_deleted=True hides record)
  ```

**Test Template**:
```python
# [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-DB-T01]

import pytest
from backend.app.infrastructure.models.news import News, NewsStatus, NewsScope


class TestNewsModel:
    def test_create_news_with_defaults(self, db_session, sample_user):
        news = News(
            title="Test Article",
            author_id=sample_user.id
        )
        db_session.add(news)
        db_session.commit()
        
        assert news.id is not None
        assert news.status == NewsStatus.DRAFT
        assert news.scope == NewsScope.GENERAL
        assert news.is_deleted is False

    def test_news_status_enum_values(self):
        assert NewsStatus.DRAFT.value == "DRAFT"
        assert NewsStatus.PUBLISHED.value == "PUBLISHED"
        assert NewsStatus.ARCHIVED.value == "ARCHIVED"

    def test_news_scope_enum_values(self):
        assert NewsScope.GENERAL.value == "GENERAL"
        assert NewsScope.INTERNAL.value == "INTERNAL"
```

---

### Task 6: Update DataModel.md
- **Purpose**: Document the new schema in project specs. `NM-ADMIN-001-DB-T01` documentation deliverable.
- **Prerequisites**: Tasks 3-5 complete
- **Artifacts impacted**: 
  - `specs/DataModel.md`
- **Test types**: Manual review
- **BDD Acceptance**:
  ```
  Given the migration is applied and tested
  When I update specs/DataModel.md
  Then the news table is documented with all columns
  And the ER diagram includes the news entity
  And relationships to users table are shown
  ```

**DataModel.md Section to Add**:
```markdown
## News

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| title | VARCHAR(255) | NOT NULL | Article headline |
| summary | VARCHAR(500) | NULL | Brief description for lists |
| content | TEXT | NULL | Rich text article body |
| status | ENUM | NOT NULL, DEFAULT 'DRAFT' | DRAFT, PUBLISHED, ARCHIVED |
| scope | ENUM | NOT NULL, DEFAULT 'GENERAL' | GENERAL, INTERNAL |
| author_id | UUID | FK → users.id, NOT NULL | Creator reference |
| cover_url | VARCHAR(2048) | NULL | Cover image URL |
| published_at | TIMESTAMPTZ | NULL | When article was published |
| created_at | TIMESTAMPTZ | NOT NULL | Row creation time |
| updated_at | TIMESTAMPTZ | NOT NULL | Last modification time |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT FALSE | Soft delete flag |

### Indexes
- `ix_news_status` on `status`
- `ix_news_scope` on `scope`
- `ix_news_is_deleted` on `is_deleted`
- `ix_news_published_at` on `published_at`
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Migration Up | `docker compose exec backend alembic upgrade head` | Exit code 0, table created |
| Migration Down | `docker compose exec backend alembic downgrade -1` | Exit code 0, table dropped |
| Model Tests | `docker compose exec backend pytest tests/integration/test_news_model.py -v` | All tests pass |

### Manual Verification
1. Connect to database: `docker compose exec db psql -U postgres -d appdb`
2. Verify table exists: `\d news`
3. Verify enums: `\dT+ news_status` and `\dT+ news_scope`
4. Verify indexes: `\di` and look for `ix_news_*`

---

## 6) Rollback Plan

If issues are discovered after deployment:
1. Run `alembic downgrade -1` to revert the migration
2. The downgrade drops the `news` table and both enums
3. No data loss in other tables (this is a new table)
