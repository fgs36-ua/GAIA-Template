# NM-PUBLIC-002-FE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-PUBLIC-002-FE-T01**  
**Related user story**: **NM-PUBLIC-002** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All components must include inline references to `NM-PUBLIC-002-FE-T01`

---

## 1) Context & Objective

### Ticket Summary
Add search input and pagination controls to the news list page. Key requirements:
- Search input with debounce (300ms)
- Pagination component with page numbers
- URL state synchronization (query params)
- Preserve search across page navigation

**Business Value**: Users can efficiently find articles through search and navigate large result sets with pagination.

### Impacted Components
| Component | Type | Operation |
|-----------|------|-----------|
| `SearchInput` | Component | CREATE |
| `Pagination` | Component | CREATE (or use shadcn/ui) |
| `useSearchParams` | Hook | CREATE (URL sync) |
| `NewsListPage` | Page | MODIFY |
| `useNewsList` | API Hook | MODIFY (add search param) |

### Impacted BDD Scenarios
This ticket implements:
- **"User searches news by title"** — Search input filters results
- **"Pagination works correctly"** — Navigate between pages
- **"URL reflects search state"** — Shareable/bookmarkable URLs

---

## 2) Scope

### In Scope
- `SearchInput` with debounce (300ms delay)
- Pagination component (pages, prev/next)
- URL query param sync (`?search=...&page=1`)
- Update `useNewsList` to accept search param
- Reset to page 1 when search changes
- Component tests

### Out of Scope
- Advanced filters (date range, tags)
- Infinite scroll
- Search suggestions/autocomplete

### Assumptions
1. **BE-T01 is complete**: API supports `search`, `skip`, `limit` params
2. **FE-T01 is complete**: NewsListPage exists with basic layout
3. **shadcn/ui Pagination**: May use existing component

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Component tests for SearchInput**:
   - Test renders input
   - Test debounces onChange
   - Test clears search

2. **Component tests for NewsListPage**:
   - Test search updates URL
   - Test pagination navigation
   - Test page resets on new search

#### Phase 2: GREEN — Minimal Implementation
1. Create useUrlSearchParams hook
2. Create SearchInput component
3. Create/configure Pagination
4. Update NewsListPage with search state
5. Run tests to verify GREEN state

### 3.2 NFR Hooks

#### Accessibility (A11y)
- Search input has label (visible or aria-label)
- Pagination has aria-current for current page
- Focus management on search clear

#### UX/Brand
- Spanish labels and placeholders
- Loading state during search
- Responsive layout

---

## 4) Atomic Task Breakdown

### Task 1: Create useUrlSearchParams Hook
- **Purpose**: Sync component state with URL query params.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `frontend/src/hooks/useUrlSearchParams.ts`
  - `frontend/src/hooks/index.ts`
- **Test types**: Unit
- **BDD Acceptance**:
  ```
  Given URL is /noticias?search=navidad&page=2
  When I use useUrlSearchParams()
  Then I get { search: "navidad", page: 2 }
  
  When I update search to "verano"
  Then URL becomes /noticias?search=verano&page=1
  ```

**Hook Template**:
```typescript
// [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-FE-T01]

import { useSearchParams } from 'react-router-dom';
import { useCallback, useMemo } from 'react';

interface NewsListParams {
  search: string;
  page: number;
}

export function useNewsListParams() {
  const [searchParams, setSearchParams] = useSearchParams();

  const params: NewsListParams = useMemo(() => ({
    search: searchParams.get('search') || '',
    page: parseInt(searchParams.get('page') || '1', 10),
  }), [searchParams]);

  const setSearch = useCallback((search: string) => {
    setSearchParams((prev) => {
      const params = new URLSearchParams(prev);
      if (search) {
        params.set('search', search);
      } else {
        params.delete('search');
      }
      params.set('page', '1'); // Reset to page 1
      return params;
    });
  }, [setSearchParams]);

  const setPage = useCallback((page: number) => {
    setSearchParams((prev) => {
      const params = new URLSearchParams(prev);
      params.set('page', String(page));
      return params;
    });
  }, [setSearchParams]);

  return {
    ...params,
    setSearch,
    setPage,
  };
}
```

---

### Task 2: Create SearchInput Component
- **Purpose**: Debounced search input with clear button.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `frontend/src/components/ui/SearchInput.tsx`
  - OR `frontend/src/features/news/components/SearchInput.tsx`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  # Scenario: Debounced typing
  Given I type "nav" then "navidad" quickly
  When 300ms passes
  Then onChange fires once with "navidad"
  
  # Scenario: Clear button
  Given search has value "navidad"
  When I click clear button
  Then value is empty and onChange fires
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-FE-T01]

import { useState, useEffect, useCallback } from 'react';
import { Search, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  debounceMs?: number;
}

export function SearchInput({
  value,
  onChange,
  placeholder = 'Buscar...',
  debounceMs = 300,
}: SearchInputProps) {
  const [localValue, setLocalValue] = useState(value);

  // Sync local value when external value changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  // Debounced onChange
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localValue !== value) {
        onChange(localValue);
      }
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [localValue, value, onChange, debounceMs]);

  const handleClear = useCallback(() => {
    setLocalValue('');
    onChange('');
  }, [onChange]);

  return (
    <div className="relative flex items-center">
      <Search 
        className="absolute left-3 h-4 w-4 text-muted-foreground"
        aria-hidden="true"
      />
      <Input
        type="search"
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        placeholder={placeholder}
        className="pl-10 pr-10"
        aria-label="Buscar noticias"
      />
      {localValue && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="absolute right-1 h-7 w-7"
          onClick={handleClear}
          aria-label="Limpiar búsqueda"
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
```

---

### Task 3: Create/Configure Pagination Component
- **Purpose**: Page navigation with numbers and prev/next.
- **Prerequisites**: None
- **Artifacts impacted**: 
  - `frontend/src/components/ui/NewsPagination.tsx`
- **Test types**: Component
- **BDD Acceptance**:
  ```
  # Scenario: Display pages
  Given total=50, limit=10, page=2
  Then I see pages 1,2,3,4,5
  And page 2 is highlighted
  
  # Scenario: Navigate
  When I click page 3
  Then onPageChange(3) is called
  
  # Scenario: Prev/Next
  Given page=2
  Then Prev and Next buttons are enabled
  When I click Next
  Then onPageChange(3) is called
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-FE-T01]

import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from '@/components/ui/pagination';

interface NewsPaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function NewsPagination({
  currentPage,
  totalPages,
  onPageChange,
}: NewsPaginationProps) {
  if (totalPages <= 1) return null;

  // Calculate visible page numbers
  const getPageNumbers = () => {
    const pages: (number | 'ellipsis')[] = [];
    const maxVisible = 5;
    
    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);
      
      if (currentPage > 3) {
        pages.push('ellipsis');
      }
      
      // Show pages around current
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      
      if (currentPage < totalPages - 2) {
        pages.push('ellipsis');
      }
      
      // Always show last page
      pages.push(totalPages);
    }
    
    return pages;
  };

  const pages = getPageNumbers();

  return (
    <Pagination>
      <PaginationContent>
        <PaginationItem>
          <PaginationPrevious 
            href="#"
            onClick={(e) => {
              e.preventDefault();
              if (currentPage > 1) onPageChange(currentPage - 1);
            }}
            aria-disabled={currentPage === 1}
            className={currentPage === 1 ? 'pointer-events-none opacity-50' : ''}
          />
        </PaginationItem>

        {pages.map((page, idx) => (
          <PaginationItem key={idx}>
            {page === 'ellipsis' ? (
              <PaginationEllipsis />
            ) : (
              <PaginationLink
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  onPageChange(page);
                }}
                isActive={page === currentPage}
                aria-current={page === currentPage ? 'page' : undefined}
              >
                {page}
              </PaginationLink>
            )}
          </PaginationItem>
        ))}

        <PaginationItem>
          <PaginationNext
            href="#"
            onClick={(e) => {
              e.preventDefault();
              if (currentPage < totalPages) onPageChange(currentPage + 1);
            }}
            aria-disabled={currentPage === totalPages}
            className={currentPage === totalPages ? 'pointer-events-none opacity-50' : ''}
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
}
```

---

### Task 4: Update useNewsList Hook
- **Purpose**: Add search parameter to the query hook.
- **Prerequisites**: Task 1
- **Artifacts impacted**: 
  - `frontend/src/features/news/api/useNewsList.ts`
- **Test types**: Unit
- **BDD Acceptance**:
  ```
  Given I call useNewsList({ search: "navidad", page: 2 })
  When API is called
  Then query params include search=navidad&skip=20&limit=20
  ```

**Updated Hook Template**:
```typescript
// [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-FE-T01]

import { useQuery } from '@tanstack/react-query';
import { http } from '@/api/http';

export interface NewsListParams {
  search?: string;
  page?: number;
  limit?: number;
}

export interface NewsListResponse {
  items: NewsListItem[];
  total: number;
  skip: number;
  limit: number;
}

const PAGE_SIZE = 20;

async function fetchNewsList(params: NewsListParams): Promise<NewsListResponse> {
  const { search, page = 1, limit = PAGE_SIZE } = params;
  const skip = (page - 1) * limit;
  
  const response = await http.get<NewsListResponse>('/api/news', {
    params: { 
      search: search || undefined, // Don't send empty string
      skip, 
      limit,
    },
  });
  return response.data;
}

export function useNewsList(params: NewsListParams = {}) {
  return useQuery({
    queryKey: ['news', 'list', params],
    queryFn: () => fetchNewsList(params),
    keepPreviousData: true, // Smoother pagination UX
  });
}
```

---

### Task 5: Update NewsListPage
- **Purpose**: Integrate search and pagination into page.
- **Prerequisites**: Tasks 1, 2, 3, 4
- **Artifacts impacted**: 
  - `frontend/src/features/news/pages/NewsListPage.tsx`
- **Test types**: Component
- **BDD Acceptance**:
  ```
  # Scenario: Search
  Given I type "navidad" in search
  When debounce fires
  Then URL updates to ?search=navidad&page=1
  And list shows filtered results
  
  # Scenario: Pagination
  Given 50 total results
  When I click page 3
  Then URL updates to ?page=3
  And list shows page 3 results
  
  # Scenario: Search resets page
  Given page=3
  When I type new search term
  Then page resets to 1
  ```

**Updated Page Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-FE-T01]

import { useNewsListParams } from '@/hooks/useUrlSearchParams';
import { useNewsList } from '../api/useNewsList';
import { NewsCard } from '../components/NewsCard';
import { NewsCardSkeleton } from '../components/NewsCardSkeleton';
import { SearchInput } from '@/components/ui/SearchInput';
import { NewsPagination } from '@/components/ui/NewsPagination';
import { Newspaper } from 'lucide-react';

const PAGE_SIZE = 20;

export function NewsListPage() {
  const { search, page, setSearch, setPage } = useNewsListParams();
  
  const { data, isLoading, isError, error, isFetching } = useNewsList({
    search,
    page,
    limit: PAGE_SIZE,
  });

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <h1 className="text-3xl font-bold">Noticias</h1>
        
        {/* Search input */}
        <div className="w-full sm:w-72">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Buscar noticias..."
          />
        </div>
      </div>

      {/* Results count */}
      {data && !isLoading && (
        <p className="text-sm text-muted-foreground mb-4">
          {data.total === 0 
            ? 'No se encontraron resultados'
            : `${data.total} noticia${data.total !== 1 ? 's' : ''} encontrada${data.total !== 1 ? 's' : ''}`}
        </p>
      )}

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
        <div className="text-center py-12 text-destructive" role="alert">
          <p>Error al cargar las noticias</p>
          <p className="text-sm">{error?.message}</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && data?.items.length === 0 && (
        <div className="text-center py-16" aria-live="polite">
          <Newspaper 
            className="mx-auto h-16 w-16 text-muted-foreground mb-4" 
            aria-hidden="true"
          />
          <p className="text-xl text-muted-foreground">
            {search 
              ? `No hay noticias que coincidan con "${search}"`
              : 'No hay noticias disponibles'}
          </p>
        </div>
      )}

      {/* News grid */}
      {!isLoading && !isError && data && data.items.length > 0 && (
        <>
          <div 
            className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${isFetching ? 'opacity-50' : ''}`}
            role="feed"
            aria-label="Lista de noticias"
          >
            {data.items.map((article) => (
              <NewsCard key={article.id} article={article} />
            ))}
          </div>

          {/* Pagination */}
          <div className="mt-8 flex justify-center">
            <NewsPagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </div>
        </>
      )}
    </div>
  );
}
```

---

### Task 6: Write Component Tests
- **Purpose**: RTL tests for SearchInput, Pagination, and updated page.
- **Prerequisites**: Tasks 2, 3, 5
- **Artifacts impacted**: 
  - `frontend/src/components/ui/__tests__/SearchInput.test.tsx`
  - `frontend/src/features/news/pages/__tests__/NewsListPage.test.tsx`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  When I run npm run test -- SearchInput NewsListPage
  Then all tests pass
  ```

**SearchInput Test Template**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-FE-T01]

import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SearchInput } from '../SearchInput';

describe('SearchInput', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders with placeholder', () => {
    render(<SearchInput value="" onChange={() => {}} placeholder="Buscar..." />);
    expect(screen.getByPlaceholderText('Buscar...')).toBeInTheDocument();
  });

  it('debounces onChange', () => {
    const handleChange = vi.fn();
    render(<SearchInput value="" onChange={handleChange} debounceMs={300} />);
    
    const input = screen.getByRole('searchbox');
    fireEvent.change(input, { target: { value: 'nav' } });
    fireEvent.change(input, { target: { value: 'navi' } });
    fireEvent.change(input, { target: { value: 'navid' } });
    fireEvent.change(input, { target: { value: 'navida' } });
    fireEvent.change(input, { target: { value: 'navidad' } });
    
    expect(handleChange).not.toHaveBeenCalled();
    
    act(() => {
      vi.advanceTimersByTime(300);
    });
    
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange).toHaveBeenCalledWith('navidad');
  });

  it('shows clear button when has value', () => {
    render(<SearchInput value="test" onChange={() => {}} />);
    expect(screen.getByLabelText('Limpiar búsqueda')).toBeInTheDocument();
  });

  it('clears value on clear button click', () => {
    const handleChange = vi.fn();
    render(<SearchInput value="test" onChange={handleChange} />);
    
    fireEvent.click(screen.getByLabelText('Limpiar búsqueda'));
    
    expect(handleChange).toHaveBeenCalledWith('');
  });

  it('has accessible label', () => {
    render(<SearchInput value="" onChange={() => {}} />);
    expect(screen.getByLabelText('Buscar noticias')).toBeInTheDocument();
  });
});
```

**NewsListPage Search Tests**:
```tsx
// [Feature: News Management] [Story: NM-PUBLIC-002] [Ticket: NM-PUBLIC-002-FE-T01]

describe('NewsListPage - Search and Pagination', () => {
  it('displays search input', () => {
    // Mock useNewsList
    renderPage();
    expect(screen.getByPlaceholderText('Buscar noticias...')).toBeInTheDocument();
  });

  it('displays results count', () => {
    mockUseNewsList({ data: { items: [mockArticle], total: 42 } });
    renderPage();
    expect(screen.getByText('42 noticias encontradas')).toBeInTheDocument();
  });

  it('displays empty search message', () => {
    mockUseNewsList({ data: { items: [], total: 0 } });
    renderPage('/noticias?search=nonexistent');
    expect(screen.getByText(/No hay noticias que coincidan/)).toBeInTheDocument();
  });

  it('displays pagination when multiple pages', () => {
    mockUseNewsList({ data: { items: mockItems, total: 100 } });
    renderPage();
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });

  it('hides pagination when single page', () => {
    mockUseNewsList({ data: { items: mockItems, total: 5 } });
    renderPage();
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
  });
});
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| SearchInput | `docker compose exec frontend npm run test -- SearchInput` | All pass |
| Pagination | `docker compose exec frontend npm run test -- NewsPagination` | All pass |
| Page Tests | `docker compose exec frontend npm run test -- NewsListPage` | All pass |
| All Frontend | `docker compose exec frontend npm run test` | All pass |

### Manual Verification
1. Start frontend: `docker compose up -d`
2. Navigate to: `http://localhost:5188/noticias`
3. **Search**:
   - Type "navidad" in search box
   - Wait 300ms for debounce
   - Verify URL updates to `?search=navidad&page=1`
   - Verify filtered results appear
4. **Clear search**:
   - Click X button in search
   - Verify search clears and shows all results
5. **Pagination**:
   - With many results, click page 3
   - Verify URL updates to `?page=3`
   - Verify correct page of results
6. **Search + Pagination**:
   - Navigate to page 3
   - Type new search term
   - Verify page resets to 1
7. **Shareable URL**:
   - Copy URL with search and page
   - Open in new tab
   - Verify same state loads

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `frontend/src/hooks/useUrlSearchParams.ts` | CREATE |
| `frontend/src/hooks/index.ts` | MODIFY |
| `frontend/src/components/ui/SearchInput.tsx` | CREATE |
| `frontend/src/components/ui/NewsPagination.tsx` | CREATE |
| `frontend/src/features/news/api/useNewsList.ts` | MODIFY |
| `frontend/src/features/news/pages/NewsListPage.tsx` | MODIFY |
| `frontend/src/components/ui/__tests__/SearchInput.test.tsx` | CREATE |
| `frontend/src/features/news/pages/__tests__/NewsListPage.test.tsx` | MODIFY |

---

## 7) Brand Compliance Checklist

| Element | Spanish Text |
|---------|--------------|
| Search placeholder | "Buscar noticias..." |
| Search label | "Buscar noticias" (aria-label) |
| Clear button label | "Limpiar búsqueda" |
| Results count (singular) | "1 noticia encontrada" |
| Results count (plural) | "42 noticias encontradas" |
| No results | "No se encontraron resultados" |
| No results with search | "No hay noticias que coincidan con '{search}'" |

---

## 8) Accessibility Checklist (WCAG AA)

| Requirement | Implementation |
|-------------|----------------|
| Search label | aria-label on input |
| Clear button | Accessible name |
| Pagination | nav with aria-label |
| Current page | aria-current="page" |
| Disabled buttons | aria-disabled + visual |
| Loading state | aria-busy + opacity change |
