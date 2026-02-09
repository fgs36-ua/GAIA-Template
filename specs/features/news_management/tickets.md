# News Management — Implementation Tickets

**Feature:** News Management (Módulo de Noticias)  
**Slug:** `news_management`  
**Source:** `user-stories.md`

## Global Dependencies
- **User Management** must be implemented (auth, RBAC with Admin/Member/Supporter/Visitor roles)
- Database infrastructure (PostgreSQL + Alembic migrations)

---

## Story: NM-ADMIN-001 — Create News Article

**Source**: `user-stories.md#NM-ADMIN-001`  
**Key Scenarios**: Successfully create draft, Missing title validation, XSS sanitization, Audit logging

### Tickets for NM-ADMIN-001

1. - [x] (2026-02-09) **NM-ADMIN-001-DB-T01 — Create News table and enums**
   - **Type**: DB
   - **Description**: Create the `news` table with all required fields to support article creation. Implements data model from feature-descr.md Annex.
   - **Scope**:
     - Included: `news` table, `NewsStatus` enum (DRAFT, PUBLISHED, ARCHIVED), `NewsScope` enum (GENERAL, INTERNAL), FK to users table, soft delete flag
     - Excluded: Tags table (future), Attachments table (future)
   - **Dependencies**: User Management DB schema (for `author_id` FK)
   - **Deliverables**:
     - Alembic migration script
     - SQLAlchemy model `News` in `infrastructure/models/news.py`
     - Update `specs/DataModel.md`

2. - [x] (2026-02-09) **NM-ADMIN-001-BE-T01 — Create News endpoint (POST /api/news)**
   - **Type**: BE
   - **Description**: Implement POST endpoint to create a news article as draft. Enforces Admin-only access, validates required fields, sanitizes rich text content.
   - **Scope**:
     - Included: POST endpoint, Pydantic schemas (CreateNewsRequest, NewsResponse), XSS sanitization, audit logging
     - Excluded: File upload, Tags
   - **Dependencies**: NM-ADMIN-001-DB-T01
   - **Deliverables**:
     - Domain entity `News` in `domain/entities/news.py`
     - Repository interface `NewsRepository` in `domain/repositories/`
     - Use case `CreateNewsUseCase` in `application/use_cases/news/`
     - Repository impl in `infrastructure/repositories/`
     - Router endpoint in `presentation/api/news.py`
     - Pydantic schemas in `presentation/schemas/news.py`
     - Unit tests (use case), Integration tests (repository)
   - **Security**: Admin role check, input sanitization (bleach/html-sanitizer)
   - **Observability**: Audit log entry on create

3. - [x] **NM-ADMIN-001-FE-T01 — News creation form UI** (2026-02-09)
   - **Type**: FE
   - **Description**: Build the news creation form with title, summary, rich text editor, and scope selector. Integrates with backend POST endpoint.
   - **Scope**:
     - Included: Form page, React Quill integration, Zod validation, TanStack Query mutation
     - Excluded: Cover image upload, Tags input
   - **Dependencies**: NM-ADMIN-001-BE-T01
   - **Deliverables**:
     - Page component `NewsFormPage` in `features/news/pages/`
     - Form component `NewsForm` in `features/news/components/`
     - API hook `useCreateNews` in `features/news/api/`
     - Zod schema for validation
     - Component tests (Vitest + RTL)
   - **A11y**: Label associations, error announcements

---

## Story: NM-ADMIN-002 — Edit News Article

**Source**: `user-stories.md#NM-ADMIN-002`  
**Key Scenarios**: Edit draft, Edit published (preserve published_at), Non-admin blocked

### Tickets for NM-ADMIN-002

1. - [ ] **NM-ADMIN-002-BE-T01 — Update News endpoint (PUT /api/news/{id})**
   - **Type**: BE
   - **Description**: Implement PUT endpoint to update an existing article. Preserves `published_at` for published articles. Admin-only access.
   - **Scope**:
     - Included: PUT endpoint, UpdateNewsRequest schema, ownership/admin validation
     - Excluded: Partial updates (PATCH)
   - **Dependencies**: NM-ADMIN-001-DB-T01, NM-ADMIN-001-BE-T01
   - **Deliverables**:
     - Use case `UpdateNewsUseCase`
     - Updated router with PUT handler
     - Pydantic schema `UpdateNewsRequest`
     - Unit tests, Integration tests
   - **Security**: Admin role check, 403 for non-admins

2. - [ ] **NM-ADMIN-002-FE-T01 — News edit form UI**
   - **Type**: FE
   - **Description**: Extend news form to support edit mode. Pre-populate fields from existing article.
   - **Scope**:
     - Included: Edit mode in NewsFormPage, useUpdateNews mutation, fetch existing article
     - Excluded: Version conflict handling
   - **Dependencies**: NM-ADMIN-002-BE-T01, NM-ADMIN-001-FE-T01
   - **Deliverables**:
     - Updated `NewsFormPage` with edit mode
     - API hook `useUpdateNews`, `useNewsById`
     - Component tests

---

## Story: NM-ADMIN-003 — Publish News Article

**Source**: `user-stories.md#NM-ADMIN-003`  
**Key Scenarios**: Publish sets published_at, Cannot publish without summary, Fast operation

### Tickets for NM-ADMIN-003

1. - [ ] **NM-ADMIN-003-BE-T01 — Publish News endpoint (POST /api/news/{id}/publish)**
   - **Type**: BE
   - **Description**: Implement action endpoint to transition article from DRAFT to PUBLISHED. Sets `published_at` timestamp.
   - **Scope**:
     - Included: POST action endpoint, business rule validation (summary required), status transition
     - Excluded: Scheduled publishing
   - **Dependencies**: NM-ADMIN-001-DB-T01
   - **Deliverables**:
     - Use case `PublishNewsUseCase`
     - Router action endpoint
     - Unit tests, Integration tests
   - **Performance**: Operation must complete <500ms

2. - [ ] **NM-ADMIN-003-FE-T01 — Publish button and workflow**
   - **Type**: FE
   - **Description**: Add publish button to article detail/edit view. Shows confirmation and success message.
   - **Scope**:
     - Included: Publish button, usePublishNews mutation, success toast
     - Excluded: Publish scheduling UI
   - **Dependencies**: NM-ADMIN-003-BE-T01
   - **Deliverables**:
     - Updated article detail component
     - API hook `usePublishNews`
     - Component tests

---

## Story: NM-ADMIN-004 — Archive News Article

**Source**: `user-stories.md#NM-ADMIN-004`  
**Key Scenarios**: Archive hides from list, Restore to draft

### Tickets for NM-ADMIN-004

1. - [ ] **NM-ADMIN-004-BE-T01 — Archive/Restore News endpoints**
   - **Type**: BE
   - **Description**: Implement action endpoints to archive (PUBLISHED→ARCHIVED) and restore (ARCHIVED→DRAFT) articles.
   - **Scope**:
     - Included: POST /api/news/{id}/archive, POST /api/news/{id}/restore
     - Excluded: Bulk archive
   - **Dependencies**: NM-ADMIN-001-DB-T01
   - **Deliverables**:
     - Use cases `ArchiveNewsUseCase`, `RestoreNewsUseCase`
     - Router action endpoints
     - Unit tests, Integration tests

2. - [ ] **NM-ADMIN-004-FE-T01 — Archive/Restore buttons**
   - **Type**: FE
   - **Description**: Add archive button for published articles and restore button for archived articles.
   - **Scope**:
     - Included: Conditional buttons based on status, mutations, success messages
     - Excluded: Archived list filter (covered in NM-PUBLIC-002)
   - **Dependencies**: NM-ADMIN-004-BE-T01
   - **Deliverables**:
     - Updated article actions component
     - API hooks `useArchiveNews`, `useRestoreNews`
     - Component tests

---

## Story: NM-ADMIN-005 — Delete News Article (Soft Delete)

**Source**: `user-stories.md#NM-ADMIN-005`  
**Key Scenarios**: Soft delete sets is_deleted, Cancel dialog, Audit logging

### Tickets for NM-ADMIN-005

1. - [ ] **NM-ADMIN-005-BE-T01 — Delete News endpoint (DELETE /api/news/{id})**
   - **Type**: BE
   - **Description**: Implement soft delete endpoint. Sets `is_deleted=true` instead of physical deletion.
   - **Scope**:
     - Included: DELETE endpoint, soft delete logic, audit logging
     - Excluded: Hard delete, Undo
   - **Dependencies**: NM-ADMIN-001-DB-T01
   - **Deliverables**:
     - Use case `DeleteNewsUseCase`
     - Router DELETE handler
     - Repository method with soft delete
     - Unit tests, Integration tests
   - **Observability**: Audit log with DELETE action

2. - [ ] **NM-ADMIN-005-FE-T01 — Delete button with confirmation dialog**
   - **Type**: FE
   - **Description**: Add delete button with AlertDialog confirmation. Shows success message after deletion.
   - **Scope**:
     - Included: Delete button, AlertDialog, useDeleteNews mutation
     - Excluded: Bulk delete
   - **Dependencies**: NM-ADMIN-005-BE-T01
   - **Deliverables**:
     - Delete confirmation component
     - API hook `useDeleteNews`
     - Component tests

---

## Story: NM-MEMBER-001 — View Internal News

**Source**: `user-stories.md#NM-MEMBER-001`  
**Key Scenarios**: Member sees all, Supporter sees General only, API filters at DB level

### Tickets for NM-MEMBER-001

1. - [ ] **NM-MEMBER-001-BE-T01 — Scope-filtered news list endpoint**
   - **Type**: BE
   - **Description**: Modify GET /api/news to filter based on user role. Members see all, others see only GENERAL scope. **Filtering MUST happen at query level.**
   - **Scope**:
     - Included: Role-based query filtering, scope parameter for admins
     - Excluded: Per-article permission caching
   - **Dependencies**: NM-ADMIN-001-DB-T01, User Management (role resolution)
   - **Deliverables**:
     - Use case `ListNewsUseCase` with role-aware filtering
     - Repository query with scope filter
     - Unit tests, Integration tests
   - **Security**: INTERNAL scope NEVER returned to non-members. Filtering at SQL level, not Python.

2. - [ ] **NM-MEMBER-001-FE-T01 — News list with scope badges**
   - **Type**: FE
   - **Description**: Display news list with "Socios" badge for internal articles. Only visible to Members.
   - **Scope**:
     - Included: Badge component, conditional rendering based on scope
     - Excluded: Scope filter tabs (covered in NM-PUBLIC-002)
   - **Dependencies**: NM-MEMBER-001-BE-T01
   - **Deliverables**:
     - `NewsCard` component with scope badge
     - Updated list component
     - Component tests

---

## Story: NM-PUBLIC-001 — View General News

**Source**: `user-stories.md#NM-PUBLIC-001`  
**Key Scenarios**: Visitor/Supporter sees General, Empty state, Accessibility

### Tickets for NM-PUBLIC-001

1. - [ ] **NM-PUBLIC-001-BE-T01 — Public news list endpoint (GET /api/news)**
   - **Type**: BE
   - **Description**: Implement GET endpoint for listing published news. Unauthenticated users see only GENERAL + PUBLISHED articles.
   - **Scope**:
     - Included: GET endpoint, pagination (skip/limit), sorting (date DESC), status filter (PUBLISHED only for non-admins)
     - Excluded: Cursor pagination
   - **Dependencies**: NM-ADMIN-001-DB-T01
   - **Deliverables**:
     - Use case `ListNewsUseCase`
     - Pydantic schemas `NewsListResponse`, `PaginatedResponse`
     - Router GET handler
     - Unit tests, Integration tests
   - **Performance**: <500ms p95

2. - [ ] **NM-PUBLIC-001-BE-T02 — News detail endpoint (GET /api/news/{id})**
   - **Type**: BE
   - **Description**: Implement GET endpoint for article detail. Enforces scope-based access control.
   - **Scope**:
     - Included: GET by ID, 403 for unauthorized internal access, 404 for deleted
     - Excluded: View tracking (future)
   - **Dependencies**: NM-ADMIN-001-DB-T01
   - **Deliverables**:
     - Use case `GetNewsDetailUseCase`
     - Router GET handler
     - Unit tests, Integration tests

3. - [ ] **NM-PUBLIC-001-FE-T01 — News list page**
   - **Type**: FE
   - **Description**: Build the public news list page with cards, loading skeleton, and empty state.
   - **Scope**:
     - Included: List page, NewsCard, Skeleton loading, empty state message
     - Excluded: Search input (NM-PUBLIC-002)
   - **Dependencies**: NM-PUBLIC-001-BE-T01
   - **Deliverables**:
     - Page `NewsListPage` in `features/news/pages/`
     - Component `NewsCard` in `features/news/components/`
     - API hook `useNewsList`
     - Component tests
   - **A11y**: Heading hierarchy, alt text for covers, keyboard navigation

4. - [ ] **NM-PUBLIC-001-FE-T02 — News detail page**
   - **Type**: FE
   - **Description**: Build the article detail page showing full content with proper heading structure.
   - **Scope**:
     - Included: Detail page, rich text rendering, cover image, back navigation
     - Excluded: Related articles
   - **Dependencies**: NM-PUBLIC-001-BE-T02
   - **Deliverables**:
     - Page `NewsDetailPage` in `features/news/pages/`
     - API hook `useNewsById`
     - Component tests
   - **A11y**: Semantic HTML, screen reader friendly

---

## Story: NM-PUBLIC-002 — Search and Filter News

**Source**: `user-stories.md#NM-PUBLIC-002`  
**Key Scenarios**: Title search, Pagination, Performance, No results

### Tickets for NM-PUBLIC-002

1. - [ ] **NM-PUBLIC-002-BE-T01 — News search and pagination**
   - **Type**: BE
   - **Description**: Add search (title ILIKE) and pagination parameters to news list endpoint.
   - **Scope**:
     - Included: `search` query param, `skip`/`limit` pagination, total count in response
     - Excluded: Full-text search, tag filtering
   - **Dependencies**: NM-PUBLIC-001-BE-T01
   - **Deliverables**:
     - Updated `ListNewsUseCase` with search
     - Updated repository query
     - Updated schemas with pagination metadata
     - Unit tests, Integration tests
   - **Performance**: <500ms p95 with pagination

2. - [ ] **NM-PUBLIC-002-FE-T01 — Search input and pagination controls**
   - **Type**: FE
   - **Description**: Add search input and pagination to news list. Use URL state for query params.
   - **Scope**:
     - Included: Search input with debounce, pagination component, URL sync
     - Excluded: Advanced filters (date range, tags)
   - **Dependencies**: NM-PUBLIC-002-BE-T01, NM-PUBLIC-001-FE-T01
   - **Deliverables**:
     - Search input component
     - Pagination component
     - Updated `NewsListPage` with search state
     - Component tests

---

## Ticket Summary

| Story | DB | BE | FE | Total |
|-------|----|----|----|----|
| NM-ADMIN-001 | 1 | 1 | 1 | 3 |
| NM-ADMIN-002 | 0 | 1 | 1 | 2 |
| NM-ADMIN-003 | 0 | 1 | 1 | 2 |
| NM-ADMIN-004 | 0 | 1 | 1 | 2 |
| NM-ADMIN-005 | 0 | 1 | 1 | 2 |
| NM-MEMBER-001 | 0 | 1 | 1 | 2 |
| NM-PUBLIC-001 | 0 | 2 | 2 | 4 |
| NM-PUBLIC-002 | 0 | 1 | 1 | 2 |
| **Total** | **1** | **9** | **9** | **19** |

---

## Implementation Order (Recommended)

```
NM-ADMIN-001-DB-T01 (DB Foundation)
    │
    ├── NM-ADMIN-001-BE-T01 → NM-ADMIN-001-FE-T01
    │
    ├── NM-PUBLIC-001-BE-T01 → NM-PUBLIC-001-FE-T01
    │   └── NM-PUBLIC-001-BE-T02 → NM-PUBLIC-001-FE-T02
    │       └── NM-PUBLIC-002-BE-T01 → NM-PUBLIC-002-FE-T01
    │
    ├── NM-ADMIN-002-BE-T01 → NM-ADMIN-002-FE-T01
    ├── NM-ADMIN-003-BE-T01 → NM-ADMIN-003-FE-T01
    ├── NM-ADMIN-004-BE-T01 → NM-ADMIN-004-FE-T01
    ├── NM-ADMIN-005-BE-T01 → NM-ADMIN-005-FE-T01
    │
    └── NM-MEMBER-001-BE-T01 → NM-MEMBER-001-FE-T01
```
