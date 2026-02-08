# NM-ADMIN-002-FE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-ADMIN-002-FE-T01**  
**Related user story**: **NM-ADMIN-002** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All components must include inline references to `NM-ADMIN-002-FE-T01`

---

## 1) Context & Objective

### Ticket Summary
Extend the existing news form to support edit mode. Key requirements:
- Add route `/admin/news/:id/edit` for editing
- Fetch existing article data and pre-populate form fields
- Use TanStack Query mutation for update API call
- Reuse existing `NewsForm` component from NM-ADMIN-001-FE-T01
- Handle loading states while fetching article data

**Business Value**: Enables Administrators to correct errors or update information in news articles through the existing form interface.

### Impacted Components
| Component | Type | Operation |
|-----------|------|-----------|
| `NewsFormPage` | Page | MODIFY (add edit mode) |
| `useUpdateNews` | API Hook | CREATE |
| `useNewsById` | API Hook | CREATE |

### Impacted BDD Scenarios
This ticket implements the UI for:
- **"Successfully edit a draft article"** — Pre-populate, submit, success feedback
- **"Edit a published article"** — Same flow, no UI difference
- **"Non-admin cannot access edit form"** — Route protection (existing auth)

---

## 2) Scope

### In Scope
- Route `/admin/news/:id/edit`
- `useNewsById` query hook to fetch article
- `useUpdateNews` mutation hook for PUT call
- Modified `NewsFormPage` to detect edit vs create mode
- Loading skeleton while fetching article
- 404 handling if article not found
- Success toast on update
- Component tests

### Out of Scope
- Version conflict handling (optimistic locking)
- Concurrent edit warnings
- New NewsForm component (reuse existing)

### Assumptions
1. **FE-T01 is complete**: `NewsForm` and `NewsFormPage` exist
2. **BE-T01 is complete**: GET `/api/news/{id}` and PUT `/api/news/{id}` exist
3. **React Router is configured**: Can add new route

### Open Questions
1. **Q1**: Is there a GET `/api/news/{id}` endpoint?
   - **If No**: Need to add it in a separate task
   - **Assumption**: Will be implemented as part of list/detail tickets or add here

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for useNewsById**:
   - Test query returns article data
   - Test loading state
   - Test error state (404)

2. **Unit tests for useUpdateNews**:
   - Test mutation calls correct endpoint
   - Test success callback
   - Test error handling

3. **Component tests for NewsFormPage (edit mode)**:
   - Test form is pre-populated with article data
   - Test loading skeleton is shown while fetching
   - Test submit calls update mutation

#### Phase 2: GREEN — Minimal Implementation
1. Create API hooks
2. Update NewsFormPage for edit mode
3. Add route
4. Run tests to verify GREEN state

#### Phase 3: REFACTOR
1. Polish loading states
2. Ensure consistent error handling

### 3.2 NFR Hooks

#### Accessibility (A11y)
- Loading state announced to screen readers
- Form maintains accessibility from create mode

#### UX/Brand
- Spanish labels and messages
- Page title changes: "Editar Noticia" vs "Crear Noticia"
- Success message: "Cambios guardados"

---

## 4) Atomic Task Breakdown

### Task 1: Create useNewsById Query Hook
- **Purpose**: Fetch existing article for edit form. TanStack Query.
- **Prerequisites**: GET endpoint exists (or add stub)
- **Artifacts impacted**: 
  - `frontend/src/features/news/api/useNewsById.ts`
  - `frontend/src/features/news/api/index.ts`
- **Test types**: Unit (MSW mock)
- **BDD Acceptance**:
  ```
  Given a valid article ID
  When I call useNewsById(id)
  Then I receive the article data
  And isLoading is false when complete
  
  Given an invalid article ID
  When I call useNewsById(id)
  Then isError is true
  ```

**Hook Template**:
```typescript
// [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-FE-T01]

import { useQuery } from '@tanstack/react-query';
import { http } from '@/api/http';

interface NewsArticle {
  id: string;
  title: string;
  summary: string | null;
  content: string | null;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  scope: 'GENERAL' | 'INTERNAL';
  authorId: string;
  coverUrl: string | null;
  publishedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

async function fetchNewsById(id: string): Promise<NewsArticle> {
  const response = await http.get<NewsArticle>(`/api/news/${id}`);
  return response.data;
}

export function useNewsById(id: string | undefined) {
  return useQuery({
    queryKey: ['news', id],
    queryFn: () => fetchNewsById(id!),
    enabled: !!id,
  });
}
```

---

### Task 2: Create useUpdateNews Mutation Hook
- **Purpose**: TanStack Query mutation for PUT /api/news/{id}. Supports BDD scenario "Successfully edit a draft article".
- **Prerequisites**: PUT endpoint exists
- **Artifacts impacted**: 
  - `frontend/src/features/news/api/useUpdateNews.ts`
  - `frontend/src/features/news/api/index.ts`
- **Test types**: Unit (MSW mock)
- **BDD Acceptance**:
  ```
  Given I call useUpdateNews.mutate({ id, data })
  When the API returns 200
  Then the mutation succeeds
  And I receive the updated news object
  And the news query is invalidated
  ```

**Hook Template**:
```typescript
// [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-FE-T01]

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { http } from '@/api/http';
import type { NewsFormData } from '../schemas/news.schema';

interface UpdateNewsParams {
  id: string;
  data: NewsFormData;
}

interface NewsResponse {
  id: string;
  title: string;
  summary: string | null;
  content: string | null;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  scope: 'GENERAL' | 'INTERNAL';
  authorId: string;
  coverUrl: string | null;
  publishedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

async function updateNews({ id, data }: UpdateNewsParams): Promise<NewsResponse> {
  const response = await http.put<NewsResponse>(`/api/news/${id}`, {
    title: data.title,
    summary: data.summary || null,
    content: data.content || null,
    scope: data.scope,
    cover_url: data.coverUrl || null,
  });
  return response.data;
}

export function useUpdateNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateNews,
    onSuccess: (data) => {
      // Invalidate specific article and list
      queryClient.invalidateQueries({ queryKey: ['news', data.id] });
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });
}
```

---

### Task 3: Update NewsFormPage for Edit Mode
- **Purpose**: Extend page to handle both create and edit modes. Core UI deliverable.
- **Prerequisites**: Tasks 1, 2
- **Artifacts impacted**: 
  - `frontend/src/features/news/pages/NewsFormPage.tsx`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  # Scenario: Edit mode pre-populates form
  Given I navigate to /admin/news/:id/edit
  When the article is loaded
  Then the form fields are pre-populated with article data
  And the page title is "Editar Noticia"
  
  # Scenario: Loading state while fetching
  Given I navigate to /admin/news/:id/edit
  When the article is being fetched
  Then I see a loading skeleton
  
  # Scenario: Submit calls update mutation
  Given I am editing an article
  When I modify fields and click "Guardar Cambios"
  Then the update mutation is called
  And I see success message "Cambios guardados"
  ```

**Updated Page Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-FE-T01]

import { useNavigate, useParams } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { NewsForm } from '../components/NewsForm';
import { useCreateNews } from '../api/useCreateNews';
import { useUpdateNews } from '../api/useUpdateNews';
import { useNewsById } from '../api/useNewsById';
import type { NewsFormData } from '../schemas/news.schema';

export function NewsFormPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { id } = useParams<{ id: string }>();
  
  const isEditMode = !!id;
  
  // Fetch existing article for edit mode
  const { data: article, isLoading, isError } = useNewsById(id);
  
  // Mutations
  const createNews = useCreateNews();
  const updateNews = useUpdateNews();
  
  const handleSubmit = (data: NewsFormData) => {
    if (isEditMode && id) {
      updateNews.mutate({ id, data }, {
        onSuccess: () => {
          toast({
            title: 'Cambios guardados',
            description: 'La noticia ha sido actualizada',
          });
          navigate('/admin/news');
        },
        onError: () => {
          toast({
            title: 'Error',
            description: 'No se pudo actualizar la noticia. Intenta de nuevo.',
            variant: 'destructive',
          });
        },
      });
    } else {
      createNews.mutate(data, {
        onSuccess: () => {
          toast({
            title: 'Noticia guardada',
            description: 'Noticia guardada como borrador',
          });
          navigate('/admin/news');
        },
        onError: () => {
          toast({
            title: 'Error',
            description: 'No se pudo guardar la noticia. Intenta de nuevo.',
            variant: 'destructive',
          });
        },
      });
    }
  };

  // Error state (404)
  if (isEditMode && isError) {
    return (
      <div className="container max-w-3xl py-8">
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-destructive">Noticia no encontrada</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Loading state
  if (isEditMode && isLoading) {
    return (
      <div className="container max-w-3xl py-8">
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-48" />
          </CardHeader>
          <CardContent className="space-y-6">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-48 w-full" />
            <Skeleton className="h-10 w-32" />
          </CardContent>
        </Card>
      </div>
    );
  }

  // Default values for edit mode
  const defaultValues = isEditMode && article ? {
    title: article.title,
    summary: article.summary || '',
    content: article.content || '',
    scope: article.scope,
    coverUrl: article.coverUrl || '',
  } : undefined;

  return (
    <div className="container max-w-3xl py-8">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">
            {isEditMode ? 'Editar Noticia' : 'Crear Noticia'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <NewsForm
            onSubmit={handleSubmit}
            isLoading={createNews.isPending || updateNews.isPending}
            defaultValues={defaultValues}
            submitLabel={isEditMode ? 'Guardar Cambios' : 'Guardar Borrador'}
          />
        </CardContent>
      </Card>
    </div>
  );
}
```

---

### Task 4: Update NewsForm Component Props
- **Purpose**: Add support for defaultValues and custom submit label.
- **Prerequisites**: FE-T01 completed
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/NewsForm.tsx`
- **Test types**: Component
- **BDD Acceptance**:
  ```
  Given NewsForm receives defaultValues
  When the form renders
  Then all fields are pre-populated with those values
  
  Given NewsForm receives submitLabel
  When the form renders
  Then the submit button shows that label
  ```

**Updated Props**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-FE-T01]

interface NewsFormProps {
  onSubmit: (data: NewsFormData) => void;
  isLoading?: boolean;
  defaultValues?: Partial<NewsFormData>;
  submitLabel?: string;
}

export function NewsForm({ 
  onSubmit, 
  isLoading, 
  defaultValues,
  submitLabel = 'Guardar Borrador',
}: NewsFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<NewsFormData>({
    resolver: zodResolver(newsFormSchema),
    defaultValues: {
      title: defaultValues?.title || '',
      summary: defaultValues?.summary || '',
      content: defaultValues?.content || '',
      scope: defaultValues?.scope || 'GENERAL',
      coverUrl: defaultValues?.coverUrl || '',
    },
  });
  
  // ... rest of component
  
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* ... fields ... */}
      <div className="flex justify-end gap-4">
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Guardando...' : submitLabel}
        </Button>
      </div>
    </form>
  );
}
```

---

### Task 5: Add Edit Route
- **Purpose**: Register `/admin/news/:id/edit` route. Wiring step.
- **Prerequisites**: Task 3
- **Artifacts impacted**: 
  - `frontend/src/routes/index.tsx` or equivalent router config
- **Test types**: Manual (navigate to route)
- **BDD Acceptance**:
  ```
  Given I am logged in as Admin
  When I navigate to /admin/news/{id}/edit
  Then I see the NewsFormPage in edit mode
  ```

**Route Addition**:
```tsx
// In routes config
{
  path: '/admin/news/:id/edit',
  element: <NewsFormPage />,
  // Auth guard should already apply
}
```

---

### Task 6: Write Component Tests
- **Purpose**: RTL tests for edit mode in NewsFormPage. Supports accessibility and flow validation.
- **Prerequisites**: Tasks 3, 4
- **Artifacts impacted**: 
  - `frontend/src/features/news/pages/__tests__/NewsFormPage.test.tsx`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  Given the component tests exist
  When I run npm run test
  Then all NewsFormPage tests pass (create and edit modes)
  ```

**Test Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-FE-T01]

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NewsFormPage } from '../NewsFormPage';

// Mock hooks
vi.mock('../api/useNewsById', () => ({
  useNewsById: (id: string) => ({
    data: id ? { 
      id, 
      title: 'Existing Title', 
      summary: 'Existing summary',
      content: '<p>Existing content</p>',
      scope: 'GENERAL',
      status: 'DRAFT',
    } : undefined,
    isLoading: false,
    isError: false,
  }),
}));

vi.mock('../api/useUpdateNews', () => ({
  useUpdateNews: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}));

const queryClient = new QueryClient();

const renderWithRouter = (initialRoute: string) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/admin/news/new" element={<NewsFormPage />} />
          <Route path="/admin/news/:id/edit" element={<NewsFormPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('NewsFormPage - Edit Mode', () => {
  it('shows edit title when editing', async () => {
    renderWithRouter('/admin/news/123/edit');
    
    await waitFor(() => {
      expect(screen.getByText('Editar Noticia')).toBeInTheDocument();
    });
  });

  it('pre-populates form with article data', async () => {
    renderWithRouter('/admin/news/123/edit');
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('Existing Title')).toBeInTheDocument();
    });
  });

  it('shows "Guardar Cambios" button in edit mode', async () => {
    renderWithRouter('/admin/news/123/edit');
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /guardar cambios/i })).toBeInTheDocument();
    });
  });
});

describe('NewsFormPage - Create Mode', () => {
  it('shows create title when creating', () => {
    renderWithRouter('/admin/news/new');
    
    expect(screen.getByText('Crear Noticia')).toBeInTheDocument();
  });

  it('shows "Guardar Borrador" button in create mode', () => {
    renderWithRouter('/admin/news/new');
    
    expect(screen.getByRole('button', { name: /guardar borrador/i })).toBeInTheDocument();
  });
});
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Hook Tests | `docker compose exec frontend npm run test -- useNewsById.test.ts useUpdateNews.test.ts` | All pass |
| Page Tests | `docker compose exec frontend npm run test -- NewsFormPage.test.tsx` | All pass |
| All Frontend Tests | `docker compose exec frontend npm run test` | All pass |

### Manual Verification
1. Start frontend: `docker compose up -d`
2. Navigate to: `http://localhost:5188/admin/news`
3. Create a new article (or have one existing)
4. Click edit on an article → Navigate to `/admin/news/{id}/edit`
5. Verify:
   - [ ] Page title shows "Editar Noticia"
   - [ ] Form is pre-populated with article data
   - [ ] Rich text editor shows existing content
   - [ ] Scope selector shows current scope
   - [ ] Submit button says "Guardar Cambios"
   - [ ] Submit shows success toast "Cambios guardados"
   - [ ] Navigates back to list after save

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `frontend/src/features/news/api/useNewsById.ts` | CREATE |
| `frontend/src/features/news/api/useUpdateNews.ts` | CREATE |
| `frontend/src/features/news/api/index.ts` | MODIFY (export new hooks) |
| `frontend/src/features/news/components/NewsForm.tsx` | MODIFY (add props) |
| `frontend/src/features/news/pages/NewsFormPage.tsx` | MODIFY (add edit mode) |
| `frontend/src/routes/index.tsx` | MODIFY (add edit route) |
| `frontend/src/features/news/pages/__tests__/NewsFormPage.test.tsx` | CREATE |

---

## 7) Brand Compliance Checklist

- [ ] Title: "Editar Noticia" (Spanish)
- [ ] Success: "Cambios guardados" (Spanish)
- [ ] Error: "No se pudo actualizar la noticia" (Spanish)
- [ ] Button: "Guardar Cambios" (Spanish)
- [ ] 404 message: "Noticia no encontrada" (Spanish)
- [ ] Loading skeleton follows design system
