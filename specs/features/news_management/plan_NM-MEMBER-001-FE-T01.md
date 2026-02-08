# NM-MEMBER-001-FE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-MEMBER-001-FE-T01**  
**Related user story**: **NM-MEMBER-001** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All components must include inline references to `NM-MEMBER-001-FE-T01`

---

## 1) Context & Objective

### Ticket Summary
Display news list with scope badges for internal articles. Key requirements:
- "Socios" badge on INTERNAL articles
- Badge only visible when user is authenticated as Member/Admin
- Badge styling consistent with brand guidelines

**Business Value**: Members can easily identify exclusive internal content in the news feed.

### Impacted Components
| Component | Type | Operation |
|-----------|------|-----------|
| `ScopeBadge` | Component | CREATE |
| `NewsCard` | Component | MODIFY |
| `useAuth` | Context hook | VERIFY exists |

### Impacted BDD Scenarios
This ticket implements:
- **"Member sees marked articles"** — INTERNAL articles have visual indicator
- **"Badge styling"** — Consistent with brand

---

## 2) Scope

### In Scope
- `ScopeBadge` component with "Socios" text
- Update `NewsCard` to show badge for INTERNAL scope
- Conditional rendering based on scope field
- Component tests

### Out of Scope
- Scope filter tabs (covered in NM-PUBLIC-002)
- Admin-specific badges
- Badge click actions

### Assumptions
1. **BE-T01 is complete**: API returns `scope` field in news response
2. **FE-T01 complete**: NewsCard component exists
3. **Auth context exists**: Can check user role

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Component tests for ScopeBadge**:
   - Test renders with correct text
   - Test accessible name

2. **Component tests for NewsCard**:
   - Test shows badge for INTERNAL scope
   - Test hides badge for GENERAL scope

#### Phase 2: GREEN — Minimal Implementation
1. Create ScopeBadge component
2. Update NewsCard with conditional badge
3. Run tests to verify GREEN state

### 3.2 NFR Hooks

#### Accessibility (A11y)
- Badge has aria-label for screen readers
- Badge text readable (sufficient contrast)

#### UX/Brand
- Spanish text "Socios"
- Brand colors for badge

---

## 4) Atomic Task Breakdown

### Task 1: Create ScopeBadge Component
- **Purpose**: Reusable badge for scope indicator.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/ScopeBadge.tsx`
  - `frontend/src/features/news/components/index.ts`
- **Test types**: Component
- **BDD Acceptance**:
  ```
  Given an INTERNAL scope
  When I render ScopeBadge
  Then I see "Socios" text
  And badge has proper styling
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-MEMBER-001] [Ticket: NM-MEMBER-001-FE-T01]

import { Badge } from '@/components/ui/badge';

type NewsScope = 'GENERAL' | 'INTERNAL';

interface ScopeBadgeProps {
  scope: NewsScope;
  className?: string;
}

const SCOPE_CONFIG = {
  INTERNAL: {
    label: 'Socios',
    ariaLabel: 'Contenido exclusivo para socios',
    variant: 'secondary' as const,
    className: 'bg-blue-100 text-blue-800 hover:bg-blue-100',
  },
  GENERAL: null, // No badge for general content
} as const;

export function ScopeBadge({ scope, className }: ScopeBadgeProps) {
  const config = SCOPE_CONFIG[scope];
  
  // No badge for GENERAL scope
  if (!config) return null;

  return (
    <Badge 
      variant={config.variant}
      className={`${config.className} ${className || ''}`}
      aria-label={config.ariaLabel}
    >
      {config.label}
    </Badge>
  );
}
```

---

### Task 2: Update NewsCard Component
- **Purpose**: Show scope badge on cards.
- **Prerequisites**: Task 1
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/NewsCard.tsx`
- **Test types**: Component
- **BDD Acceptance**:
  ```
  # Scenario: INTERNAL article
  Given article with scope "INTERNAL"
  When I render NewsCard
  Then I see "Socios" badge
  
  # Scenario: GENERAL article
  Given article with scope "GENERAL"
  When I render NewsCard
  Then I do NOT see any badge
  ```

**Updated Component Template**:
```tsx
// [Feature: News Management] [Story: NM-MEMBER-001] [Ticket: NM-MEMBER-001-FE-T01]

import { Link } from 'react-router-dom';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { formatDate } from '@/lib/utils/date';
import { ScopeBadge } from './ScopeBadge';
import type { NewsListItem } from '../api/useNewsList';

interface NewsCardProps {
  article: NewsListItem;
}

export function NewsCard({ article }: NewsCardProps) {
  const { id, title, summary, scope, coverImageUrl, publishedAt } = article;

  return (
    <Link 
      to={`/noticias/${id}`}
      className="block focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-lg"
    >
      <Card className="h-full hover:shadow-lg transition-shadow duration-200">
        {/* Cover image */}
        {coverImageUrl && (
          <div className="aspect-video overflow-hidden rounded-t-lg relative">
            <img
              src={coverImageUrl}
              alt={`Imagen de ${title}`}
              className="w-full h-full object-cover"
              loading="lazy"
            />
            {/* Badge overlay on image */}
            <div className="absolute top-2 right-2">
              <ScopeBadge scope={scope} />
            </div>
          </div>
        )}
        
        <CardHeader className="relative">
          {/* Badge in header if no cover image */}
          {!coverImageUrl && scope === 'INTERNAL' && (
            <div className="mb-2">
              <ScopeBadge scope={scope} />
            </div>
          )}
          <h2 className="text-lg font-semibold line-clamp-2">{title}</h2>
        </CardHeader>
        
        {summary && (
          <CardContent>
            <p className="text-muted-foreground text-sm line-clamp-3">
              {summary}
            </p>
          </CardContent>
        )}
        
        <CardFooter>
          <time 
            dateTime={publishedAt || undefined}
            className="text-xs text-muted-foreground"
          >
            {publishedAt ? formatDate(publishedAt) : 'Borrador'}
          </time>
        </CardFooter>
      </Card>
    </Link>
  );
}
```

---

### Task 3: Update NewsDetailPage Badge
- **Purpose**: Show scope badge on detail page header.
- **Prerequisites**: Task 1
- **Artifacts impacted**: 
  - `frontend/src/features/news/pages/NewsDetailPage.tsx`
- **Test types**: Component
- **BDD Acceptance**:
  ```
  Given viewing INTERNAL article detail
  When page loads
  Then I see "Socios" badge near the title
  ```

**Updated Detail Page Snippet**:
```tsx
// [Feature: News Management] [Story: NM-MEMBER-001] [Ticket: NM-MEMBER-001-FE-T01]

// In the header section, replace the inline badge with ScopeBadge:

<header className="mb-8">
  <div className="flex items-center gap-3 mb-4">
    <h1 className="text-3xl md:text-4xl font-bold">
      {article.title}
    </h1>
  </div>
  
  {/* Meta info */}
  <div className="flex items-center gap-4 text-sm text-muted-foreground">
    {article.publishedAt && (
      <time dateTime={article.publishedAt}>
        {formatDate(article.publishedAt)}
      </time>
    )}
    <ScopeBadge scope={article.scope} />
  </div>
</header>
```

---

### Task 4: Write Component Tests
- **Purpose**: RTL tests for ScopeBadge and updated NewsCard.
- **Prerequisites**: Tasks 1, 2
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/__tests__/ScopeBadge.test.tsx`
  - `frontend/src/features/news/components/__tests__/NewsCard.test.tsx`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  When I run npm run test -- ScopeBadge NewsCard
  Then all tests pass
  ```

**ScopeBadge Test Template**:
```tsx
// [Feature: News Management] [Story: NM-MEMBER-001] [Ticket: NM-MEMBER-001-FE-T01]

import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ScopeBadge } from '../ScopeBadge';

describe('ScopeBadge', () => {
  it('renders "Socios" for INTERNAL scope', () => {
    render(<ScopeBadge scope="INTERNAL" />);
    expect(screen.getByText('Socios')).toBeInTheDocument();
  });

  it('returns null for GENERAL scope', () => {
    const { container } = render(<ScopeBadge scope="GENERAL" />);
    expect(container).toBeEmptyDOMElement();
  });

  it('has accessible label for INTERNAL', () => {
    render(<ScopeBadge scope="INTERNAL" />);
    expect(screen.getByLabelText('Contenido exclusivo para socios')).toBeInTheDocument();
  });
});
```

**NewsCard Badge Test**:
```tsx
// [Feature: News Management] [Story: NM-MEMBER-001] [Ticket: NM-MEMBER-001-FE-T01]

describe('NewsCard - Scope Badge', () => {
  it('shows badge for INTERNAL scope', () => {
    renderCard({ ...mockArticle, scope: 'INTERNAL' });
    expect(screen.getByText('Socios')).toBeInTheDocument();
  });

  it('does not show badge for GENERAL scope', () => {
    renderCard({ ...mockArticle, scope: 'GENERAL' });
    expect(screen.queryByText('Socios')).not.toBeInTheDocument();
  });

  it('positions badge on cover image when present', () => {
    renderCard({ 
      ...mockArticle, 
      scope: 'INTERNAL',
      coverImageUrl: '/test.jpg',
    });
    // Badge should be in overlay position
    const badge = screen.getByText('Socios');
    expect(badge.closest('.absolute')).toBeInTheDocument();
  });
});
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| ScopeBadge | `docker compose exec frontend npm run test -- ScopeBadge` | All pass |
| NewsCard Badge | `docker compose exec frontend npm run test -- NewsCard` | All pass |
| All Frontend | `docker compose exec frontend npm run test` | All pass |

### Manual Verification
1. Start frontend: `docker compose up -d`
2. **As Member**:
   - Login as member
   - Navigate to `/noticias`
   - Verify INTERNAL articles show "Socios" badge
   - Verify GENERAL articles have no badge
3. **Badge positioning**:
   - Verify badge appears on cover image overlay (top-right)
   - Verify badge appears in header if no cover image
4. **Detail page**:
   - Click on INTERNAL article
   - Verify badge visible in detail header
5. **Accessibility**:
   - Tab to badge
   - Screen reader should announce "Contenido exclusivo para socios"

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `frontend/src/features/news/components/ScopeBadge.tsx` | CREATE |
| `frontend/src/features/news/components/index.ts` | MODIFY (export) |
| `frontend/src/features/news/components/NewsCard.tsx` | MODIFY |
| `frontend/src/features/news/pages/NewsDetailPage.tsx` | MODIFY |
| `frontend/src/features/news/components/__tests__/ScopeBadge.test.tsx` | CREATE |
| `frontend/src/features/news/components/__tests__/NewsCard.test.tsx` | MODIFY |

---

## 7) Brand Compliance Checklist

| Element | Spanish Text |
|---------|--------------|
| Badge label | "Socios" |
| Badge aria-label | "Contenido exclusivo para socios" |

| Style | Value |
|-------|-------|
| Background | `bg-blue-100` |
| Text color | `text-blue-800` |
| Variant | secondary |

---

## 8) Accessibility Checklist (WCAG AA)

| Requirement | Implementation |
|-------------|----------------|
| Aria label | "Contenido exclusivo para socios" |
| Color contrast | Blue-800 on Blue-100 (passes) |
| Visible text | "Socios" readable label |
| Screen reader | Badge announces purpose |
