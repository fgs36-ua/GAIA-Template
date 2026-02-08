# NM-PUBLIC-001-FE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-PUBLIC-001-FE-T01**  
**Related user story**: **NM-PUBLIC-001** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All components must include inline references to `NM-PUBLIC-001-FE-T01`

---

## 1) Context & Objective

### Ticket Summary
Build the public news list page with cards, loading states, and empty state. Key requirements:
- News list page accessible to all users (including anonymous)
- Card-based layout with cover image, title, summary, date
- Skeleton loading during fetch
- Empty state message: "No hay noticias disponibles"
- WCAG AA accessibility compliance

**Business Value**: Visitors and members can browse news articles in an engaging, accessible format.

### Impacted Components
| Component | Type | Operation |
|-----------|------|-----------|
| `useNewsList` | API Hook | CREATE |
| `NewsCard` | Component | CREATE |
| `NewsCardSkeleton` | Component | CREATE |
| `NewsListPage` | Page | CREATE |

### Impacted BDD Scenarios
This ticket implements:
- **"Visitor can view general news"** — See list of articles
- **"Empty news list"** — See "No hay noticias disponibles"
- **"News list is accessible"** — Heading hierarchy, alt text, keyboard nav

---

## 2) Scope

### In Scope
- `useNewsList` query hook with TanStack Query
- `NewsCard` component (cover, title, summary, date, link)
- `NewsCardSkeleton` for loading state
- `NewsListPage` with responsive grid
- Empty state message in Spanish
- Accessibility: heading levels, alt text, keyboard navigation
- Component tests

### Out of Scope
- Search input (NM-PUBLIC-002)
- Filter tabs (NM-PUBLIC-002)
- Pagination controls (future enhancement)
- Infinite scroll

### Assumptions
1. **BE-T01 is complete**: GET /api/news endpoint exists
2. **shadcn/ui Card**: Available for styling
3. **React Router**: For Link to detail page

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Component tests for NewsCard**:
   - Test renders title, summary, date
   - Test cover image with alt text
   - Test link to detail page

2. **Component tests for NewsListPage**:
   - Test shows skeleton while loading
   - Test shows cards when data loads
   - Test shows empty state when no articles

#### Phase 2: GREEN — Minimal Implementation
1. Create API hook
2. Create NewsCard + Skeleton
3. Create NewsListPage
4. Run tests to verify GREEN state

### 3.2 NFR Hooks

#### Accessibility (A11y)
- Heading hierarchy: h1 for page title, h2 for each card
- Alt text for cover images (use title as fallback)
- Card is focusable and clickable via keyboard

#### UX/Brand
- Spanish text for all UI elements
- Responsive grid (1 col mobile, 2 tablet, 3 desktop)
- Brand color for links and hover states

---

## 4) Atomic Task Breakdown

### Task 1: Create useNewsList Query Hook
- **Purpose**: TanStack Query hook for GET /api/news with pagination.
- **Prerequisites**: BE-T01 complete
- **Artifacts impacted**: 
  - `frontend/src/features/news/api/useNewsList.ts`
  - `frontend/src/features/news/api/index.ts`
- **Test types**: Unit (MSW mock)
- **BDD Acceptance**:
  ```
  Given I call useNewsList()
  When the API returns data
  Then I receive items and total count
  ```

**Hook Template**:
```typescript
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T01]

import { useQuery } from '@tanstack/react-query';
import { http } from '@/api/http';

export interface NewsListItem {
  id: string;
  title: string;
  summary: string | null;
  scope: 'GENERAL' | 'INTERNAL';
  status: string;
  coverImageUrl: string | null;
  publishedAt: string | null;
  authorId: string;
  createdAt: string;
}

export interface NewsListResponse {
  items: NewsListItem[];
  total: number;
  skip: number;
  limit: number;
}

interface UseNewsListParams {
  skip?: number;
  limit?: number;
}

async function fetchNewsList(params: UseNewsListParams): Promise<NewsListResponse> {
  const { skip = 0, limit = 20 } = params;
  const response = await http.get<NewsListResponse>('/api/news', {
    params: { skip, limit },
  });
  return response.data;
}

export function useNewsList(params: UseNewsListParams = {}) {
  return useQuery({
    queryKey: ['news', 'list', params],
    queryFn: () => fetchNewsList(params),
  });
}
```

---

### Task 2: Create NewsCard Component
- **Purpose**: Display individual news article as a card.
- **Prerequisites**: None (presentational)
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/NewsCard.tsx`
  - `frontend/src/features/news/components/index.ts`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  # Scenario: Renders article info
  Given a news article
  When I render NewsCard
  Then I see the title as h2
  And I see the summary
  And I see the formatted date
  And I see the cover image (if exists)
  
  # Scenario: Link to detail
  When I click the card
  Then I navigate to /noticias/{id}
  
  # Scenario: Accessible
  Then the cover image has alt text
  And the whole card is keyboard navigable
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T01]

import { Link } from 'react-router-dom';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { formatDate } from '@/lib/utils/date';
import type { NewsListItem } from '../api/useNewsList';

interface NewsCardProps {
  article: NewsListItem;
}

export function NewsCard({ article }: NewsCardProps) {
  const { id, title, summary, coverImageUrl, publishedAt } = article;

  return (
    <Link 
      to={`/noticias/${id}`}
      className="block focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-lg"
    >
      <Card className="h-full hover:shadow-lg transition-shadow duration-200">
        {coverImageUrl && (
          <div className="aspect-video overflow-hidden rounded-t-lg">
            <img
              src={coverImageUrl}
              alt={`Imagen de ${title}`}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          </div>
        )}
        <CardHeader>
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

### Task 3: Create NewsCardSkeleton Component
- **Purpose**: Loading placeholder for news cards.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/NewsCardSkeleton.tsx`
  - `frontend/src/features/news/components/index.ts`
- **Test types**: Snapshot (optional)
- **BDD Acceptance**:
  ```
  Given page is loading
  When I render NewsCardSkeleton
  Then I see animated placeholder shapes
  And skeleton has proper aria attributes
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T01]

import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function NewsCardSkeleton() {
  return (
    <Card className="h-full" aria-busy="true" aria-label="Cargando noticia">
      <div className="aspect-video">
        <Skeleton className="w-full h-full rounded-t-lg" />
      </div>
      <CardHeader>
        <Skeleton className="h-6 w-3/4" />
      </CardHeader>
      <CardContent className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </CardContent>
      <CardFooter>
        <Skeleton className="h-3 w-24" />
      </CardFooter>
    </Card>
  );
}
```

---

### Task 4: Create NewsListPage Component
- **Purpose**: Main page with grid of news cards.
- **Prerequisites**: Tasks 1, 2, 3
- **Artifacts impacted**: 
  - `frontend/src/features/news/pages/NewsListPage.tsx`
  - `frontend/src/features/news/pages/index.ts`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  # Scenario: Loading state
  Given the page is loading
  Then I see skeleton cards
  
  # Scenario: With articles
  Given articles exist
  When the page loads
  Then I see a grid of NewsCard components
  
  # Scenario: Empty state
  Given no articles exist
  When the page loads
  Then I see "No hay noticias disponibles"
  
  # Scenario: Heading hierarchy
  Then the page has h1 "Noticias"
  And each card has h2 for the title
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T01]

import { useNewsList } from '../api/useNewsList';
import { NewsCard } from '../components/NewsCard';
import { NewsCardSkeleton } from '../components/NewsCardSkeleton';
import { Newspaper } from 'lucide-react';

export function NewsListPage() {
  const { data, isLoading, isError, error } = useNewsList();

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Page title */}
      <h1 className="text-3xl font-bold mb-8">Noticias</h1>

      {/* Loading state */}
      {isLoading && (
        <div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          aria-live="polite"
          aria-busy="true"
        >
          {Array.from({ length: 6 }).map((_, i) => (
            <NewsCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div 
          className="text-center py-12 text-destructive"
          role="alert"
        >
          <p>Error al cargar las noticias</p>
          <p className="text-sm">{error?.message}</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && data?.items.length === 0 && (
        <div 
          className="text-center py-16"
          aria-live="polite"
        >
          <Newspaper 
            className="mx-auto h-16 w-16 text-muted-foreground mb-4" 
            aria-hidden="true"
          />
          <p className="text-xl text-muted-foreground">
            No hay noticias disponibles
          </p>
        </div>
      )}

      {/* News grid */}
      {!isLoading && !isError && data && data.items.length > 0 && (
        <div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          role="feed"
          aria-label="Lista de noticias"
        >
          {data.items.map((article) => (
            <NewsCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}
```

---

### Task 5: Add Route Configuration
- **Purpose**: Register /noticias route in router.
- **Prerequisites**: Task 4
- **Artifacts impacted**: 
  - `frontend/src/routes/index.tsx` (or routes config file)
- **Test types**: E2E (manual verification)
- **BDD Acceptance**:
  ```
  Given I navigate to /noticias
  Then I see the NewsListPage
  ```

**Route Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T01]

import { NewsListPage } from '@/features/news/pages/NewsListPage';

// Add to routes array:
{
  path: '/noticias',
  element: <NewsListPage />,
}
```

---

### Task 6: Create Date Utility Function
- **Purpose**: Format ISO date to Spanish locale.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `frontend/src/lib/utils/date.ts`
- **Test types**: Unit
- **BDD Acceptance**:
  ```
  Given ISO date "2026-02-08T10:30:00Z"
  When I call formatDate()
  Then I get "8 de febrero de 2026"
  ```

**Utility Template**:
```typescript
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T01]

export function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('es-ES', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}
```

---

### Task 7: Write Component Tests
- **Purpose**: RTL tests for NewsCard and NewsListPage.
- **Prerequisites**: Tasks 2, 4
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/__tests__/NewsCard.test.tsx`
  - `frontend/src/features/news/pages/__tests__/NewsListPage.test.tsx`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  When I run npm run test -- NewsCard NewsListPage
  Then all tests pass
  ```

**NewsCard Test Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T01]

import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { NewsCard } from '../NewsCard';

const mockArticle = {
  id: '123',
  title: 'Test Article Title',
  summary: 'This is a test summary',
  scope: 'GENERAL' as const,
  status: 'PUBLISHED',
  coverImageUrl: '/images/test.jpg',
  publishedAt: '2026-02-08T10:30:00Z',
  authorId: 'author-1',
  createdAt: '2026-02-07T09:00:00Z',
};

const renderCard = (article = mockArticle) => {
  return render(
    <BrowserRouter>
      <NewsCard article={article} />
    </BrowserRouter>
  );
};

describe('NewsCard', () => {
  it('renders title as h2', () => {
    renderCard();
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Test Article Title');
  });

  it('renders summary', () => {
    renderCard();
    expect(screen.getByText('This is a test summary')).toBeInTheDocument();
  });

  it('renders cover image with alt text', () => {
    renderCard();
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('alt', 'Imagen de Test Article Title');
  });

  it('links to detail page', () => {
    renderCard();
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/noticias/123');
  });

  it('handles missing cover image', () => {
    renderCard({ ...mockArticle, coverImageUrl: null });
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  it('handles missing summary', () => {
    renderCard({ ...mockArticle, summary: null });
    expect(screen.queryByText('This is a test summary')).not.toBeInTheDocument();
  });
});
```

**NewsListPage Test Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-001] [Ticket: NM-PUBLIC-001-FE-T01]

import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi } from 'vitest';
import { NewsListPage } from '../NewsListPage';

vi.mock('../../api/useNewsList', () => ({
  useNewsList: vi.fn(),
}));

import { useNewsList } from '../../api/useNewsList';

const queryClient = new QueryClient();

const renderPage = () => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <NewsListPage />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('NewsListPage', () => {
  it('shows skeletons while loading', () => {
    (useNewsList as any).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });
    
    renderPage();
    expect(screen.getAllByLabelText('Cargando noticia')).toHaveLength(6);
  });

  it('shows empty state when no articles', async () => {
    (useNewsList as any).mockReturnValue({
      data: { items: [], total: 0, skip: 0, limit: 20 },
      isLoading: false,
      isError: false,
    });
    
    renderPage();
    expect(screen.getByText('No hay noticias disponibles')).toBeInTheDocument();
  });

  it('shows articles when data loads', () => {
    (useNewsList as any).mockReturnValue({
      data: {
        items: [
          {
            id: '1',
            title: 'Test Article',
            summary: 'Summary',
            scope: 'GENERAL',
            status: 'PUBLISHED',
            coverImageUrl: null,
            publishedAt: '2026-02-08T10:00:00Z',
            authorId: 'user-1',
            createdAt: '2026-02-07T09:00:00Z',
          },
        ],
        total: 1,
        skip: 0,
        limit: 20,
      },
      isLoading: false,
      isError: false,
    });
    
    renderPage();
    expect(screen.getByRole('heading', { name: 'Noticias' })).toBeInTheDocument();
    expect(screen.getByText('Test Article')).toBeInTheDocument();
  });

  it('has proper heading hierarchy', () => {
    (useNewsList as any).mockReturnValue({
      data: { items: [], total: 0, skip: 0, limit: 20 },
      isLoading: false,
      isError: false,
    });
    
    renderPage();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Noticias');
  });
});
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Component Tests | `docker compose exec frontend npm run test -- NewsCard` | All pass |
| Page Tests | `docker compose exec frontend npm run test -- NewsListPage` | All pass |
| Date Utility | `docker compose exec frontend npm run test -- date` | All pass |
| All Frontend Tests | `docker compose exec frontend npm run test` | All pass |

### Manual Verification
1. Start frontend: `docker compose up -d`
2. Navigate to: `http://localhost:5188/noticias`
3. **Loading state**:
   - Briefly observe skeleton cards while fetching
4. **Empty state**:
   - If no articles, verify "No hay noticias disponibles" message
5. **With articles**:
   - Verify grid of cards appears
   - Verify each card shows title, summary, date, cover image
6. **Responsiveness**:
   - Mobile: 1 column
   - Tablet: 2 columns
   - Desktop: 3 columns
7. **Accessibility**:
   - Tab through cards with keyboard
   - Verify focus ring visible
   - Test with screen reader (h1, h2 announced)

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `frontend/src/features/news/api/useNewsList.ts` | CREATE |
| `frontend/src/features/news/api/index.ts` | MODIFY (export hook) |
| `frontend/src/features/news/components/NewsCard.tsx` | CREATE |
| `frontend/src/features/news/components/NewsCardSkeleton.tsx` | CREATE |
| `frontend/src/features/news/components/index.ts` | MODIFY (exports) |
| `frontend/src/features/news/pages/NewsListPage.tsx` | CREATE |
| `frontend/src/features/news/pages/index.ts` | CREATE/MODIFY |
| `frontend/src/lib/utils/date.ts` | CREATE |
| `frontend/src/routes/index.tsx` | MODIFY (add route) |
| `frontend/src/features/news/components/__tests__/NewsCard.test.tsx` | CREATE |
| `frontend/src/features/news/pages/__tests__/NewsListPage.test.tsx` | CREATE |

---

## 7) Brand Compliance Checklist

| Element | Spanish Text |
|---------|--------------|
| Page title | "Noticias" |
| Empty state | "No hay noticias disponibles" |
| Error message | "Error al cargar las noticias" |
| Loading label | "Cargando noticia" |
| Feed label | "Lista de noticias" |
| Image alt | "Imagen de {title}" |
| Date format | "8 de febrero de 2026" |

---

## 8) Accessibility Checklist (WCAG AA)

| Requirement | Implementation |
|-------------|----------------|
| Heading hierarchy | h1 for page, h2 for cards |
| Alt text | Cover images have descriptive alt |
| Keyboard navigation | Cards focusable with Tab, Enter to activate |
| Focus indicator | focus-visible:ring-2 on links |
| Loading state | aria-busy="true", aria-live="polite" |
| Screen reader | Feed role, proper labels |
