# User Stories: News Management (Módulo de Noticias)

## Introduction

This document defines the user stories for the **News Management** feature, enabling the Association to publish and distribute relevant information to the neighborhood community.

**Linked Objectives:**
- **Increase Reach:** >40% of active users view at least 1 news item/week (Q1)
- **Timely Communication:** <10 min avg from Draft to Published (Q1)
- **Member Value:** >20% of Member sessions engage with Internal news (Q2)

**Feature Slug:** `news_management`
**Acronym:** `NM`

---

## User Stories

### NM-ADMIN-001: Create News Article

**As an** Administrator  
**I want to** create a new news article with title, summary, content, and visibility scope  
**So that** I can prepare official communications for the community

#### Acceptance Criteria

```gherkin
Feature: Create News Article

  Background:
    Given I am logged in as an Administrator

  # Happy Path
  Scenario: Successfully create a draft news article
    When I navigate to the news creation form
    And I enter a title "Asamblea General 2026"
    And I enter a summary "Convocatoria para la asamblea anual"
    And I enter rich text content with formatting
    And I select scope "Internal Association"
    And I click "Guardar Borrador"
    Then the article is saved with status "DRAFT"
    And I see a success message "Noticia guardada como borrador"
    And the article appears in my drafts list

  # Edge Case: Missing required fields
  Scenario: Attempt to create article without title
    When I navigate to the news creation form
    And I leave the title empty
    And I enter a summary "Test summary"
    And I click "Guardar Borrador"
    Then I see a validation error "El título es obligatorio"
    And the article is not saved

  # Security: XSS Prevention
  Scenario: Rich text content is sanitized
    When I enter content containing "<script>alert('xss')</script>"
    And I save the article
    Then the script tags are stripped from the stored content
    And the article content is safe to render

  # Observability: Audit logging
  Scenario: Creation is logged for audit
    When I create a news article
    Then an audit log entry is created with my user ID and timestamp
```

---

### NM-ADMIN-002: Edit News Article

**As an** Administrator  
**I want to** edit an existing news article  
**So that** I can correct errors or update information before or after publication

#### Acceptance Criteria

```gherkin
Feature: Edit News Article

  Background:
    Given I am logged in as an Administrator
    And a news article "Festival de Verano" exists with status "DRAFT"

  # Happy Path
  Scenario: Successfully edit a draft article
    When I open the article for editing
    And I change the title to "Festival de Verano 2026"
    And I click "Guardar Cambios"
    Then the article is updated with the new title
    And the updated_at timestamp is refreshed
    And I see a success message "Cambios guardados"

  # Edge Case: Edit published article
  Scenario: Edit a published article
    Given the article has status "PUBLISHED"
    When I open the article for editing
    And I modify the content
    And I click "Guardar Cambios"
    Then the changes are saved
    And the article remains in "PUBLISHED" status
    And the published_at timestamp is not changed

  # Security: Only author/admin can edit
  Scenario: Non-admin cannot access edit form
    Given I am logged in as a Member
    When I attempt to access the edit URL directly
    Then I receive a 403 Forbidden response
```

---

### NM-ADMIN-003: Publish News Article

**As an** Administrator  
**I want to** publish a draft news article  
**So that** it becomes visible to the appropriate audience

#### Acceptance Criteria

```gherkin
Feature: Publish News Article

  Background:
    Given I am logged in as an Administrator
    And a news article exists with status "DRAFT"

  # Happy Path
  Scenario: Successfully publish an article
    When I click "Publicar"
    Then the article status changes to "PUBLISHED"
    And the published_at timestamp is set to current time
    And the article appears in the public news list
    And I see a success message "Noticia publicada"

  # Edge Case: Publish article without summary
  Scenario: Cannot publish without summary
    Given the article has no summary
    When I click "Publicar"
    Then I see an error "El resumen es obligatorio para publicar"
    And the article remains in "DRAFT" status

  # Performance: Publication is fast
  Scenario: Publication completes quickly
    When I click "Publicar"
    Then the operation completes in under 500ms
```

---

### NM-ADMIN-004: Archive News Article

**As an** Administrator  
**I want to** archive a published news article  
**So that** outdated information is hidden from the main news feed

#### Acceptance Criteria

```gherkin
Feature: Archive News Article

  Background:
    Given I am logged in as an Administrator
    And a news article exists with status "PUBLISHED"

  # Happy Path
  Scenario: Successfully archive an article
    When I click "Archivar"
    Then the article status changes to "ARCHIVED"
    And the article no longer appears in the public news list
    And I see a success message "Noticia archivada"

  # Edge Case: Restore archived article
  Scenario: Restore an archived article to draft
    Given an article exists with status "ARCHIVED"
    When I click "Restaurar a Borrador"
    Then the article status changes to "DRAFT"
    And the published_at timestamp is cleared
```

---

### NM-ADMIN-005: Delete News Article (Soft Delete)

**As an** Administrator  
**I want to** delete a news article  
**So that** I can remove content that should no longer exist

#### Acceptance Criteria

```gherkin
Feature: Delete News Article

  Background:
    Given I am logged in as an Administrator
    And a news article "Evento Cancelado" exists

  # Happy Path
  Scenario: Successfully soft-delete an article
    When I click "Eliminar"
    And I confirm the deletion in the dialog
    Then the article is marked as is_deleted = true
    And the article no longer appears in any list
    And I see a success message "Noticia eliminada"

  # Edge Case: Cancel deletion
  Scenario: Cancel deletion dialog
    When I click "Eliminar"
    And I click "Cancelar" in the confirmation dialog
    Then the article is not deleted
    And I remain on the article page

  # Observability: Deletion is logged
  Scenario: Deletion is logged for audit
    When I delete the article
    Then an audit log entry is created with action "DELETE"
```

---

### NM-MEMBER-001: View Internal News

**As a** Member (Socio)  
**I want to** view internal association news  
**So that** I stay informed about exclusive member matters (assemblies, finances, voting)

#### Acceptance Criteria

```gherkin
Feature: View Internal News

  Background:
    Given internal news articles exist with scope "INTERNAL"

  # Happy Path
  Scenario: Member can view internal news
    Given I am logged in as a Member
    When I navigate to the news list
    Then I see both General and Internal news articles
    And Internal articles are marked with a badge "Socios"
    When I click on an internal article
    Then I can read the full content

  # Security: Supporter cannot view internal news
  Scenario: Supporter cannot see internal news
    Given I am logged in as a Supporter
    When I navigate to the news list
    Then I only see General news articles
    And Internal articles are not visible in the list

  # Security: Unauthenticated cannot view internal news
  Scenario: Visitor cannot see internal news
    Given I am not logged in
    When I navigate to the news list
    Then I only see General news articles
    When I attempt to access an internal article URL directly
    Then I receive a 403 Forbidden or redirect to login

  # Security: API-level filtering
  Scenario: API does not return internal news to unauthorized users
    Given I call the news list API without authentication
    Then the response only contains articles with scope "GENERAL"
    And no article with scope "INTERNAL" is included
```

---

### NM-PUBLIC-001: View General News

**As a** Visitor or Supporter  
**I want to** view general neighborhood news  
**So that** I stay informed about public community matters

#### Acceptance Criteria

```gherkin
Feature: View General News

  Background:
    Given published news articles exist with scope "GENERAL"

  # Happy Path: Visitor
  Scenario: Visitor can view general news
    Given I am not logged in
    When I navigate to the news page
    Then I see a list of published General news articles
    When I click on an article
    Then I can read the full content

  # Happy Path: Supporter
  Scenario: Supporter can view general news
    Given I am logged in as a Supporter
    When I navigate to the news page
    Then I see published General news articles
    And I can access article details

  # Accessibility: Screen reader support
  Scenario: News list is accessible
    When I navigate to the news list using a screen reader
    Then each article card has proper heading hierarchy
    And cover images have alt text
    And interactive elements are keyboard navigable

  # Edge Case: No news available
  Scenario: Empty news list
    Given no published General news articles exist
    When I navigate to the news page
    Then I see a message "No hay noticias disponibles"
```

---

### NM-PUBLIC-002: Search and Filter News

**As a** User (any role)  
**I want to** search news by title and filter by scope  
**So that** I can quickly find relevant information

#### Acceptance Criteria

```gherkin
Feature: Search and Filter News

  Background:
    Given multiple published news articles exist

  # Happy Path: Title search
  Scenario: Search by title
    When I enter "Asamblea" in the search box
    And I submit the search
    Then I see only articles with "Asamblea" in the title
    And the results are paginated

  # Happy Path: Pagination
  Scenario: Navigate paginated results
    Given more than 10 news articles exist
    When I navigate to the news list
    Then I see the first 10 articles
    And pagination controls are visible
    When I click "Siguiente"
    Then I see the next page of results

  # Performance: List responds quickly
  Scenario: List endpoint responds within SLA
    When I request the news list
    Then the response is received in under 500ms (p95)

  # Edge Case: No search results
  Scenario: Search with no matches
    When I search for "xyz123nonexistent"
    Then I see a message "No se encontraron resultados"
```

---

## Story Dependency Map

```
NM-ADMIN-001 (Create) 
    └── NM-ADMIN-002 (Edit)
    └── NM-ADMIN-003 (Publish) 
            └── NM-ADMIN-004 (Archive)
    └── NM-ADMIN-005 (Delete)

NM-ADMIN-003 (Publish) 
    └── NM-MEMBER-001 (View Internal)
    └── NM-PUBLIC-001 (View General)
            └── NM-PUBLIC-002 (Search/Filter)
```

---

## Cross-Cutting Concerns (All Stories)

| NFR | Requirement | Applicable Stories |
|-----|-------------|-------------------|
| Security | Internal news filtered at DB level | NM-MEMBER-001, NM-PUBLIC-001 |
| Security | Rich text sanitized against XSS | NM-ADMIN-001, NM-ADMIN-002 |
| Performance | List API <500ms p95 | NM-PUBLIC-002 |
| Accessibility | WCAG 2.1 AA compliance | NM-PUBLIC-001, NM-PUBLIC-002 |
| Observability | Audit logging for mutations | NM-ADMIN-001-005 |
