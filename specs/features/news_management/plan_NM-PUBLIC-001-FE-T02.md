# NM-PUBLIC-001-FE-T02 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-PUBLIC-001-FE-T02**  
**Related user story**: **NM-PUBLIC-001** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All components must include inline references to `NM-PUBLIC-001-FE-T02`

---

## 1) Context & Objective

### Ticket Summary
Build the news detail page showing full article content. Key requirements:
- Display full article with rich text content
- Cover image with proper alt text
- Back navigation to news list
- Semantic HTML (article, header, main)
- Loading and error states
- Handle 403 Forbidden for internal articles

**Business Value**: Users can read full article content with a polished, accessible reading experience.

### Impacted Components
| Component | Type | Operation |
|-----------|------|-----------|
| `useNewsById` | API Hook | CREATE |
| `NewsDetailPage` | Page | CREATE |
| `NewsDetailSkeleton` | Component | CREATE |

### Impacted BDD Scenarios
This ticket implements:
- **"Visitor can view general news"** — Click article, read full content
- **"News list is accessible"** — Screen reader friendly detail page

---

## 2) Scope

### In Scope
- `useNewsById` query hook for GET /api/news/{id}
- `NewsDetailPage` with full article layout
- Rich text content rendering (HTML from backend)
- Cover image display with alt text
- Back navigation link
- Loading skeleton
- Error state (404, 403)
- Route configuration /noticias/:id
- Component tests

### Out of Scope
- Related articles section
- Social sharing
- Comments

### Assumptions
1. **BE-T02 is complete**: GET /api/news/{id} endpoint exists
2. **Content is HTML**: Backend returns sanitized HTML for content field
3. **React Router**: useParams for route parameter

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Component tests for NewsDetailPage**:
   - Test shows skeleton while loading
   - Test shows article when data loads
   - Test shows 404 message
   - Test shows 403 message for members-only
   - Test back link navigates to list

#### Phase 2: GREEN — Minimal Implementation
1. Create API hook
2. Create skeleton component
3. Create detail page
4. Add route configuration
5. Run tests to verify GREEN state

### 3.2 NFR Hooks

#### Accessibility (A11y)
- Semantic HTML: article, header, main elements
- Heading hierarchy: h1 for title
- Images have descriptive alt text
- Back link is keyboard accessible

#### UX/Brand
- Spanish labels and messages
- Clean, readable typography
- Responsive layout

---

## 4) Atomic Task Breakdown

### Task 1: Create useNewsById Query Hook
- **Purpose**: TanStack Query hook for GET /api/news/{id}.
- **Prerequisites**: BE-T02 complete
- **Artifacts impacted**: 
  - `frontend/src/features/news/api/useNewsById.ts`
  - `frontend/src/features/news/api/index.ts`
- **Test types**: Unit (MSW mock)
- **BDD Acceptance**:
  ```
  Given I call useNewsById(id)
  When the API returns data
  Then I receive the full article detail
  ```

**Hook Template**:
```typescript
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T02]

import { useQuery } from '@tanstack/react-query';
import { http } from '@/api/http';
import { AxiosError } from 'axios';

export interface NewsDetail {
  id: string;
  title: string;
  content: string;
  summary: string | null;
  scope: 'GENERAL' | 'INTERNAL';
  status: string;
  coverImageUrl: string | null;
  publishedAt: string | null;
  authorId: string;
  createdAt: string;
  updatedAt: string;
}

async function fetchNewsById(id: string): Promise<NewsDetail> {
  const response = await http.get<NewsDetail>(`/api/news/${id}`);
  return response.data;
}

export function useNewsById(id: string | undefined) {
  return useQuery({
    queryKey: ['news', id],
    queryFn: () => fetchNewsById(id!),
    enabled: !!id,
    retry: (failureCount, error) => {
      // Don't retry on 403 or 404
      if (error instanceof AxiosError) {
        const status = error.response?.status;
        if (status === 403 || status === 404) return false;
      }
      return failureCount < 3;
    },
  });
}
```

---

### Task 2: Create NewsDetailSkeleton Component
- **Purpose**: Loading placeholder for detail page.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/NewsDetailSkeleton.tsx`
  - `frontend/src/features/news/components/index.ts`
- **Test types**: Snapshot (optional)
- **BDD Acceptance**:
  ```
  Given page is loading
  When I render NewsDetailSkeleton
  Then I see placeholder shapes for cover, title, content
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T02]

import { Skeleton } from '@/components/ui/skeleton';

export function NewsDetailSkeleton() {
  return (
    <article 
      className="container mx-auto px-4 py-8 max-w-3xl"
      aria-busy="true"
      aria-label="Cargando noticia"
    >
      {/* Cover image placeholder */}
      <Skeleton className="w-full aspect-video rounded-lg mb-8" />
      
      {/* Title placeholder */}
      <Skeleton className="h-10 w-3/4 mb-4" />
      
      {/* Meta info placeholder */}
      <Skeleton className="h-4 w-48 mb-8" />
      
      {/* Content placeholders */}
      <div className="space-y-4">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-4/5" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    </article>
  );
}
```

---

### Task 3: Create NewsDetailPage Component
- **Purpose**: Full article detail with content rendering.
- **Prerequisites**: Tasks 1, 2
- **Artifacts impacted**: 
  - `frontend/src/features/news/pages/NewsDetailPage.tsx`
  - `frontend/src/features/news/pages/index.ts`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  # Scenario: Loading state
  Given the page is loading
  Then I see the skeleton
  
  # Scenario: Article loaded
  Given a valid article ID
  When the page loads
  Then I see the full article with title, cover, content
  And the title is h1
  And there is a back link to /noticias
  
  # Scenario: Not found
  Given a non-existent article ID
  When the page loads
  Then I see "Noticia no encontrada"
  
  # Scenario: Forbidden (internal)
  Given an INTERNAL article
  When anonymous user loads page
  Then I see "Esta noticia es solo para socios"
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T02]

import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, AlertCircle, Lock } from 'lucide-react';
import { useNewsById } from '../api/useNewsById';
import { NewsDetailSkeleton } from '../components/NewsDetailSkeleton';
import { formatDate } from '@/lib/utils/date';
import { Button } from '@/components/ui/button';
import { AxiosError } from 'axios';

export function NewsDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: article, isLoading, isError, error } = useNewsById(id);

  // Loading state
  if (isLoading) {
    return <NewsDetailSkeleton />;
  }

  // Error states
  if (isError) {
    const status = (error as AxiosError)?.response?.status;
    
    // 403 Forbidden - members only
    if (status === 403) {
      return (
        <div className="container mx-auto px-4 py-16 max-w-3xl text-center">
          <Lock className="mx-auto h-16 w-16 text-muted-foreground mb-4" aria-hidden="true" />
          <h1 className="text-2xl font-bold mb-2">Contenido exclusivo para socios</h1>
          <p className="text-muted-foreground mb-6">
            Esta noticia es solo para socios de la asociación.
          </p>
          <Button asChild variant="outline">
            <Link to="/noticias">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Volver a noticias
            </Link>
          </Button>
        </div>
      );
    }

    // 404 Not Found or other errors
    return (
      <div className="container mx-auto px-4 py-16 max-w-3xl text-center">
        <AlertCircle className="mx-auto h-16 w-16 text-muted-foreground mb-4" aria-hidden="true" />
        <h1 className="text-2xl font-bold mb-2">Noticia no encontrada</h1>
        <p className="text-muted-foreground mb-6">
          La noticia que buscas no existe o ha sido eliminada.
        </p>
        <Button asChild variant="outline">
          <Link to="/noticias">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Volver a noticias
          </Link>
        </Button>
      </div>
    );
  }

  // Article loaded
  if (!article) return null;

  return (
    <article className="container mx-auto px-4 py-8 max-w-3xl">
      {/* Back navigation */}
      <nav className="mb-6">
        <Link 
          to="/noticias"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Volver a noticias
        </Link>
      </nav>

      {/* Cover image */}
      {article.coverImageUrl && (
        <figure className="mb-8">
          <img
            src={article.coverImageUrl}
            alt={`Imagen de ${article.title}`}
            className="w-full aspect-video object-cover rounded-lg"
          />
        </figure>
      )}

      {/* Article header */}
      <header className="mb-8">
        <h1 className="text-3xl md:text-4xl font-bold mb-4">
          {article.title}
        </h1>
        
        {/* Meta info */}
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          {article.publishedAt && (
            <time dateTime={article.publishedAt}>
              {formatDate(article.publishedAt)}
            </time>
          )}
          {article.scope === 'INTERNAL' && (
            <span className="inline-flex items-center px-2 py-1 rounded-full bg-blue-100 text-blue-800 text-xs font-medium">
              Solo socios
            </span>
          )}
        </div>
      </header>

      {/* Article content */}
      <main 
        className="prose prose-lg max-w-none"
        dangerouslySetInnerHTML={{ __html: article.content }}
      />
    </article>
  );
}
```

---

### Task 4: Add Route Configuration
- **Purpose**: Register /noticias/:id route in router.
- **Prerequisites**: Task 3
- **Artifacts impacted**: 
  - `frontend/src/routes/index.tsx` (or routes config file)
- **Test types**: E2E (manual verification)
- **BDD Acceptance**:
  ```
  Given I navigate to /noticias/123
  Then I see the NewsDetailPage
  ```

**Route Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T02]

import { NewsDetailPage } from '@/features/news/pages/NewsDetailPage';

// Add to routes array:
{
  path: '/noticias/:id',
  element: <NewsDetailPage />,
}
```

---

### Task 5: Add Prose Styles (if needed)
- **Purpose**: Ensure rich content has proper typography.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `frontend/tailwind.config.js` or `frontend/src/index.css`
- **Test types**: Visual (manual)
- **BDD Acceptance**:
  ```
  Given article has HTML content
  When I view the detail page
  Then headings, paragraphs, lists are properly styled
  ```

**CSS Template**:
```css
/* [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T02] */

/* If not using @tailwindcss/typography plugin */
.prose h2 { @apply text-2xl font-bold mt-8 mb-4; }
.prose h3 { @apply text-xl font-semibold mt-6 mb-3; }
.prose p { @apply mb-4 leading-relaxed; }
.prose ul { @apply list-disc pl-6 mb-4; }
.prose ol { @apply list-decimal pl-6 mb-4; }
.prose li { @apply mb-2; }
.prose a { @apply text-primary underline; }
.prose blockquote { @apply border-l-4 border-muted pl-4 italic; }
```

---

### Task 6: Write Component Tests
- **Purpose**: RTL tests for NewsDetailPage.
- **Prerequisites**: Task 3
- **Artifacts impacted**: 
  - `frontend/src/features/news/pages/__tests__/NewsDetailPage.test.tsx`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  When I run npm run test -- NewsDetailPage
  Then all tests pass
  ```

**Test Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T02]

import { render, screen } from '@testing-library/react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { NewsDetailPage } from '../NewsDetailPage';

vi.mock('../../api/useNewsById', () => ({
  useNewsById: vi.fn(),
}));

import { useNewsById } from '../../api/useNewsById';

const queryClient = new QueryClient();

const renderPage = (initialEntry = '/noticias/123') => {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/noticias/:id" element={<NewsDetailPage />} />
          <Route path="/noticias" element={<div>Lista de noticias</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('NewsDetailPage', () => {
  it('shows skeleton while loading', () => {
    (useNewsById as any).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });
    
    renderPage();
    expect(screen.getByLabelText('Cargando noticia')).toBeInTheDocument();
  });

  it('shows article when loaded', () => {
    (useNewsById as any).mockReturnValue({
      data: {
        id: '123',
        title: 'Test Article Title',
        content: '<p>This is the content</p>',
        summary: 'Summary',
        scope: 'GENERAL',
        status: 'PUBLISHED',
        coverImageUrl: '/image.jpg',
        publishedAt: '2026-02-08T10:00:00Z',
        authorId: 'author-1',
        createdAt: '2026-02-07T09:00:00Z',
        updatedAt: '2026-02-08T09:00:00Z',
      },
      isLoading: false,
      isError: false,
    });
    
    renderPage();
    
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Test Article Title');
    expect(screen.getByText('This is the content')).toBeInTheDocument();
    expect(screen.getByRole('img')).toHaveAttribute('alt', 'Imagen de Test Article Title');
  });

  it('shows back link', () => {
    (useNewsById as any).mockReturnValue({
      data: {
        id: '123',
        title: 'Test',
        content: '<p>Content</p>',
        scope: 'GENERAL',
        status: 'PUBLISHED',
      },
      isLoading: false,
      isError: false,
    });
    
    renderPage();
    
    expect(screen.getByRole('link', { name: /volver a noticias/i })).toBeInTheDocument();
  });

  it('shows not found message for 404', () => {
    const mockError = { response: { status: 404 } };
    (useNewsById as any).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: mockError,
    });
    
    renderPage();
    
    expect(screen.getByText('Noticia no encontrada')).toBeInTheDocument();
  });

  it('shows forbidden message for 403', () => {
    const mockError = { response: { status: 403 } };
    (useNewsById as any).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: mockError,
    });
    
    renderPage();
    
    expect(screen.getByText('Contenido exclusivo para socios')).toBeInTheDocument();
  });

  it('shows internal badge for internal articles', () => {
    (useNewsById as any).mockReturnValue({
      data: {
        id: '123',
        title: 'Internal News',
        content: '<p>Content</p>',
        scope: 'INTERNAL',
        status: 'PUBLISHED',
      },
      isLoading: false,
      isError: false,
    });
    
    renderPage();
    
    expect(screen.getByText('Solo socios')).toBeInTheDocument();
  });
});
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Hook Tests | `docker compose exec frontend npm run test -- useNewsById` | All pass |
| Page Tests | `docker compose exec frontend npm run test -- NewsDetailPage` | All pass |
| All Frontend Tests | `docker compose exec frontend npm run test` | All pass |

### Manual Verification
1. Start frontend: `docker compose up -d`
2. Navigate to: `http://localhost:5188/noticias`
3. **Happy path**:
   - Click on a news card
   - Verify navigation to /noticias/{id}
   - Verify full content displayed
   - Verify cover image visible
   - Verify back link works
4. **403 Forbidden**:
   - Log out
   - Navigate to internal article URL directly
   - Verify "Contenido exclusivo para socios" message
5. **404 Not Found**:
   - Navigate to /noticias/invalid-uuid
   - Verify "Noticia no encontrada" message
6. **Accessibility**:
   - Verify h1 is the article title
   - Verify cover image has alt text
   - Tab through page with keyboard

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `frontend/src/features/news/api/useNewsById.ts` | CREATE |
| `frontend/src/features/news/api/index.ts` | MODIFY (export hook) |
| `frontend/src/features/news/components/NewsDetailSkeleton.tsx` | CREATE |
| `frontend/src/features/news/components/index.ts` | MODIFY |
| `frontend/src/features/news/pages/NewsDetailPage.tsx` | CREATE |
| `frontend/src/features/news/pages/index.ts` | MODIFY |
| `frontend/src/routes/index.tsx` | MODIFY (add route) |
| `frontend/src/features/news/pages/__tests__/NewsDetailPage.test.tsx` | CREATE |
| `frontend/src/index.css` or `tailwind.config.js` | MODIFY (prose styles if needed) |

---

## 7) Brand Compliance Checklist

| Element | Spanish Text |
|---------|--------------|
| Back link | "Volver a noticias" |
| 404 title | "Noticia no encontrada" |
| 404 description | "La noticia que buscas no existe o ha sido eliminada." |
| 403 title | "Contenido exclusivo para socios" |
| 403 description | "Esta noticia es solo para socios de la asociación." |
| Internal badge | "Solo socios" |
| Loading label | "Cargando noticia" |
| Image alt | "Imagen de {title}" |

---

## 8) Accessibility Checklist (WCAG AA)

| Requirement | Implementation |
|-------------|----------------|
| Semantic HTML | `<article>`, `<header>`, `<main>`, `<nav>`, `<figure>` |
| Heading hierarchy | Single h1 for title |
| Alt text | Cover images have descriptive alt |
| Skip links | Back navigation at top |
| Focus management | Focus ring on interactive elements |
| Time element | `<time>` with datetime attribute |
