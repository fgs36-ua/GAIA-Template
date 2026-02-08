## 0) Feature Name & Summary
**Feature Name:** News Management (Módulo de Noticias)

**Executive Summary:**
- **Problem:** The community currently relies on fragmented channels (posters, social media, word of mouth), leading to misinformation or members missing critical updates.
- **Opportunity:** To establish the Association App as the "single source of truth" for neighborhood information, offering targeted content based on membership status.
- **Expected Outcome:** Increased community engagement, transparency in association actions, and efficient dissemination of both public and internal operational news.

**Fit with Vision / Product Goal:**
This feature directly supports the core mission of "fostering better communication and transparency between the board and the neighbors" by providing a reliable, official, and accessible communication channel.

---

## 1) Description of the feature
The News Management module allows the Association to publish relevant information for the neighborhood and the organization itself. It provides a simple publishing workflow for Administrators and an efficient reading experience for all other profiles (Members, Supporters, Visitors).

The core capability is to create, edit, publish, and delete news articles, with a strict distinction between "General Neighborhood" news (visible to arguably everyone) and "Internal Association" news (restricted to paid members). It enforces Role-Based Access Control (RBAC) to ensure information reaches the right audience without exposing sensitive internal matters to the public.

---

## 2) Users/Roles & Impacted Personas

| Role/Persona | Key Objectives | Tasks / Jobs-to-be-done | Current Pain | Stakeholders |
|---|---|---|---|---|
| **Administrator** | effective communication | Create, edit, publish, archive, and delete news. Manage visibility (General vs Internal). | Communicating via multiple manual channels is time-consuming and error-prone. | Board of Directors |
| **Member (Socio)** | Stay informed on all matters | Read all news (both General and Internal). Access exclusive member updates. | Feels disconnected from internal decisions or pays fees without seeing value. | - |
| **Supporter (Simpatizante)** | Know what's happening in the 'hood | Read General Neighborhood news. | Misses public events or general alerts. | - |
| **Visitor (Unregistered)** | Get general info | Read General Neighborhood news. | Has no easy way to know about the association's public activities. | - |

---

## 3) Problem / Opportunity Statement
**Context:** The neighborhood association generates two types of information: general interest (festivities, works, security) and internal interest (assemblies, accounts, internal voting).
**Problem Statement:** Our **community members** experience **confusion and lack of information** when **news is scattered**, which causes **low participation and trust** in the association.
**Why Now:** Launching the app without a communication channel would limit its utility to just "admin tasks" (payments/voting), missing the chance to drive daily engagement.

---

## 4) Objectives & Business Outcomes

| Objective / Outcome | KPI / Metric | Baseline | Target | Time Horizon | Measurement Method |
|---|---|---|---|---|---|
| **Increase Reach** | % of active users who view at least 1 news item/week | 0% (New) | > 40% | Q1 Post-Launch | Analytics events |
| **Timely Communication** | Avg. time from "Draft" to "Published" | N/A | < 10 min | Q1 | System logs |
| **Member Value** | engagement with "Internal" news vs General | N/A | > 20% of Member sessions | Q2 | Analytics (Page views by scope) |

---

## 5) Scope (In/Out)

**In scope:**
- **CRUD Operations:** Create, Edit, Delete (Soft), View Details, List.
- **Workflow States:** Draft (Borrador), Published (Publicado), Archived (Archivado).
- **Visibility Scopes:** General Neighborhood (Public) vs. Internal Association (Members Only).
- **Content:** Title, Summary, Rich Text Content, Cover Image (URL), Attachments, Tags.
- **RBAC:** Strict enforcement of visibility based on user role (Visitor/Supporter vs Member vs Admin).
- **Listing:** Pagination, Sorting (Date DESC), Simple Title Search.

**Out of scope:**
- **Interactions:** Comments, Reactions (Likes), Share to Social Media (native integration).
- **Advanced Features:** Push Notifications, Email Newsletters, RSS Feeds.
- **Editorial Workflow:** Review buckets, multi-author approval.
- **Internationalization:** Multi-language support (for this version).

**Key Assumptions:**
- A Rich Text Editor component is available or can be easily integrated into the Frontend.
- "Supporters" (Simpatizantes) are treated effectively as "Public" for news visibility, pending any future "Supporter-only" content.

**Dependencies:**
- **User Management:** Must be fully implemented to authenticate Admins and resolve Member vs Supporter roles.

---

## 6) Non-Functional Requirements (NFRs)

### 6.1 Security & Privacy
- **Access Control:** Content with scope `INTERNO_ASOCIACION` must **never** be returned by the API to unauthenticated users or Supporters. Filtering must happen at the Database/query level, not in the Frontend.
- **Sanitization:** All Rich Text input must be sanitized on the backend to prevent stored XSS attacks.

### 6.2 Performance
- **Response Time:** List endpoint (CU-05) must respond in < 500ms (p95).
- **Pagination:** List endpoint must support pagination (`skip`/`limit` or cursor) to prevent large payloads.

### 6.3 Accessibility (a11y)
- **WCAG 2.1 AA:** News detail and list views must be readable by screen readers (proper heading hierarchy `h1`-`h6`, alt text for cover images).

### 6.4 Observability
- **Audit:** Logging of who created/edited/deleted news items (Author ID, Timestamp).
- **Metrics:** Track views on Detail page to measure engagement.

---

### Annexes
- **Data Model Proposal:**
    - `id` (UUID), `title` (string), `summary` (string), `content` (text), `status` (enum: DRAFT, PUBLISHED, ARCHIVED), `scope` (enum: GENERAL, INTERNAL), `author_id` (FK), `cover_url`, `published_at` (datetime), `created_at`, `updated_at`, `is_deleted` (bool).
