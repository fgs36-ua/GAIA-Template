---
trigger: always_on
description: when defining, implementing, or verifying any feature or business logic
---

# Product Specs - Source of Truth

**Core Rule:** Do NOT rely on training data or assumptions for product features. The single source of truth for "what the product does" is the `specs/` directory.

## Directory Structure

- **`specs/PRD.md`**: High-level vision, core modules, and non-functional requirements.
- **`specs/DataModel.md`**: current datamodel of the app being developed. 
- **`specs/ArchitecturalModel.md`**: current architectural model of the app being developed. 
- **`specs/UserStories.md`**: High-level backlog and user story definitions.
- **`specs/features/<feature-name>/`**: Detailed granular user stories, tickets and implementation plans (one per ticket) for specific features.
- **`specs/progress.md`**: Log of delivered milestones.

## Guidelines

1.  **Read First**: Before implementing any feature, ALWAYS read `specs/PRD.md` and the relevant feature spec in `specs/features/`.
2.  **No Hallucinations**: If a feature is not in `specs/`, it does not exist. Ask the user before inventing it.
3.  **Traceability**: Every Pull Request implementation MUST link back to a feature defined in `specs/`.

> **Note:** If you find discrepancies between code and specs, priority goes to the Specs (ask user to update them if code is newer).

---

## Spec Writing Standards (Mandatory)

### 1. Feature Slugs
- Derive **[feature-slug]** from `Feature Name` in **kebab-case**.
- Example: “User Management” → `user-management`.

### 2. User Story Standards
- **INVEST**: Stories must be Independent, Negotiable, Valuable, Estimable, Small, and Testable.
- **BDD/Gherkin**: Acceptance criteria MUST use valid Gherkin (Given/When/Then).
  - Include scenarios for: Happy Path, Edge Cases, Security/Privacy, A11y/i18n, Error Handling.
- **IDs**: Must be stable and unique.
  - Format: `<ACRONYM>-<ROLE>-<SEQUENCE>`
  - Example: `UM-USER-001` (User Management, User role, 001).

### 3. Ticket Standards
- **Thin Vertical Slices**: Break stories into trios of tickets (DB + BE + FE) that deliver end-to-end value.
- **IDs**: `<STORY_ID>-<TYPE>-T<NN>`
  - Types: `DB`, `BE`, `FE`, `OTH`.
  - Example: `UM-USER-001-BE-T02`.
- **Traceability**: Every ticket must reference its source User Story ID and specific Gherkin scenarios.
- **Limited scope** Each ticket must affect max 1-2 files 
- **Logical order, respecting dependencies**: DB->BE->FE
- **Testability**: All tickets should be testable

### 4. NFR Mapping
- **Security**: RBAC/ABAC, encryption, PII protection must be explicit criteria.
- **Performance**: Observable thresholds (e.g., P95 latency).
- **A11y**: WCAG targets for frontend tickets.