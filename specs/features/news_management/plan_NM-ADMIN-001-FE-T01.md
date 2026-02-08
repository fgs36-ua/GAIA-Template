# NM-ADMIN-001-FE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-ADMIN-001-FE-T01**  
**Related user story**: **NM-ADMIN-001** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All components must include inline references to `NM-ADMIN-001-FE-T01`

---

## 1) Context & Objective

### Ticket Summary
Build the news creation form UI for Administrators. This includes:
- Page component with form layout
- Rich text editor (React Quill) for content
- Scope selector (GENERAL/INTERNAL)
- TanStack Query mutation for API integration
- Zod validation with Spanish error messages
- Full accessibility compliance (label associations, error announcements)

**Business Value**: Enables Administrators to create news articles through an intuitive, accessible interface that integrates with the backend API.

### Impacted Components
| Component | Type | Operation |
|-----------|------|-----------|
| `NewsFormPage` | Page | CREATE |
| `NewsForm` | Form Component | CREATE |
| `useCreateNews` | API Hook | CREATE |
| `newsSchemas` | Zod Schema | CREATE |

### Impacted BDD Scenarios
This ticket implements the UI for:
- **"Successfully create a draft news article"** — Form submission flow
- **"Attempt to create article without title"** — Validation error display
- **"Creation is logged for audit"** — Success feedback

---

## 2) Scope

### In Scope
- `NewsFormPage` in `features/news/pages/`
- `NewsForm` component in `features/news/components/`
- `useCreateNews` mutation hook in `features/news/api/`
- Zod schema for form validation
- React Quill integration for rich text
- Scope selector (dropdown: "General"/"Interno")
- Loading and error states
- Success toast notification
- Component tests (Vitest + RTL)

### Out of Scope
- Cover image upload (future ticket)
- Tags input (future ticket)
- News list page (separate ticket)
- Edit form (separate ticket)

### Assumptions
1. **BE-T01 is complete**: POST /api/news endpoint exists
2. **shadcn/ui is installed**: Button, Input, Select, Card, Label, Textarea
3. **React Quill is available**: Or will be added as dependency
4. **Routing exists**: Route to `/admin/news/new` can be added

### Open Questions
1. **Q1**: Is there an existing admin layout component to wrap the page?
   - **If Yes**: Use it. **If No**: Create a simple wrapper.
2. **Q2**: Is toast notification system already configured?
   - **Assumption**: Use shadcn/ui `toast` component or `sonner`.

---

## 3) Detailed Work Plan (TDD + BDD)

### Container Check (Prerequisites)
Before starting:
1. Verify frontend dev server runs: `npm run dev`
2. Verify backend is accessible at `VITE_API_BASE_URL`
3. Verify shadcn/ui components are available

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for Zod schema**:
   - Test validation passes with valid data
   - Test validation fails without title
   - Test title max length (255 chars)
   - Test Spanish error messages

2. **Component tests for NewsForm**:
   - Test form renders all fields
   - Test submit button is disabled when invalid
   - Test error messages appear on validation failure
   - Test accessibility (label associations)

3. **Integration tests for useCreateNews**:
   - Test mutation calls correct endpoint
   - Test success callback is invoked
   - Test error handling

#### Phase 2: GREEN — Minimal Implementation
1. Create Zod schema
2. Create API hook
3. Create form component
4. Create page component
5. Add route
6. Run tests to verify GREEN state

#### Phase 3: REFACTOR
1. Polish styling per brand guidelines
2. Improve accessibility
3. Add loading states and animations

### 3.2 NFR Hooks

#### Accessibility (A11y)
- All inputs have associated `<label>` elements
- Error messages use `aria-describedby`
- Focus management after submission
- Minimum 44×44 touch targets
- Visible focus rings (2px minimum)

#### Security
- Content sanitization happens on backend (not duplicated in FE)
- No sensitive data in local storage

#### UX/Brand
- Spanish labels and messages (Castilian)
- shadcn/ui components with brand tokens
- Inter font, 8pt grid spacing
- Primary button uses Terracotta AA color

---

## 4) Atomic Task Breakdown

### Task 1: Add React Quill Dependency
- **Purpose**: Install rich text editor library. Supports `NM-ADMIN-001-FE-T01`.
- **Prerequisites**: npm access
- **Artifacts impacted**: 
  - `frontend/package.json`
  - `frontend/src/index.css` (Quill styles import)
- **Test types**: Manual (verify import works)
- **BDD Acceptance**:
  ```
  Given I add react-quill to dependencies
  When I import ReactQuill in a component
  Then no errors occur
  And the editor renders
  ```

**Commands**:
```bash
npm install react-quill-new
```

**Global CSS Import** (in `index.css`):
```css
/* [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01] */
@import 'react-quill-new/dist/quill.snow.css';
```

---

### Task 2: Create Zod Schema
- **Purpose**: Define form validation with Spanish messages. Supports BDD scenario "Attempt to create article without title".
- **Prerequisites**: Zod installed
- **Artifacts impacted**: 
  - `frontend/src/features/news/schemas/news.schema.ts`
- **Test types**: Unit
- **BDD Acceptance**:
  ```
  # Scenario: Attempt to create article without title
  Given I have a form data object without title
  When I validate with newsFormSchema
  Then I get error "El título es obligatorio"
  ```

**Schema Template**:
```typescript
// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]

import { z } from 'zod';

export const NewsScope = {
  GENERAL: 'GENERAL',
  INTERNAL: 'INTERNAL',
} as const;

export const newsFormSchema = z.object({
  title: z
    .string()
    .min(1, 'El título es obligatorio')
    .max(255, 'El título no puede exceder 255 caracteres'),
  summary: z
    .string()
    .max(500, 'El resumen no puede exceder 500 caracteres')
    .optional()
    .nullable(),
  content: z.string().optional().nullable(),
  scope: z.enum(['GENERAL', 'INTERNAL']).default('GENERAL'),
  coverUrl: z
    .string()
    .url('La URL de portada no es válida')
    .max(2048)
    .optional()
    .nullable(),
});

export type NewsFormData = z.infer<typeof newsFormSchema>;
```

---

### Task 3: Create API Hook (useCreateNews)
- **Purpose**: TanStack Query mutation for POST /api/news. Supports BDD scenario "Successfully create a draft news article".
- **Prerequisites**: Axios instance configured
- **Artifacts impacted**: 
  - `frontend/src/features/news/api/useCreateNews.ts`
  - `frontend/src/features/news/api/index.ts`
- **Test types**: Integration (MSW mock)
- **BDD Acceptance**:
  ```
  Given I call useCreateNews.mutate() with valid data
  When the API returns 201
  Then the mutation succeeds
  And I receive the created news object
  ```

**Hook Template**:
```typescript
// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { http } from '@/api/http';
import type { NewsFormData } from '../schemas/news.schema';

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

async function createNews(data: NewsFormData): Promise<NewsResponse> {
  const response = await http.post<NewsResponse>('/api/news', {
    title: data.title,
    summary: data.summary || null,
    content: data.content || null,
    scope: data.scope,
    cover_url: data.coverUrl || null,
  });
  return response.data;
}

export function useCreateNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createNews,
    onSuccess: () => {
      // Invalidate news list queries
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });
}
```

---

### Task 4: Create NewsForm Component
- **Purpose**: Reusable form component with rich text editor. Core UI deliverable.
- **Prerequisites**: Tasks 1, 2, 3
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/NewsForm.tsx`
  - `frontend/src/features/news/components/index.ts`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  # Scenario: Form renders with all fields
  Given I render NewsForm
  Then I see input for "Título"
  And I see textarea for "Resumen"
  And I see rich text editor for "Contenido"
  And I see select for "Ámbito"
  And I see submit button "Guardar Borrador"
  
  # Scenario: Validation error displayed
  Given I submit form without title
  Then I see error "El título es obligatorio"
  And the error is associated with the title input via aria-describedby
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import ReactQuill from 'react-quill-new';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { newsFormSchema, type NewsFormData } from '../schemas/news.schema';

interface NewsFormProps {
  onSubmit: (data: NewsFormData) => void;
  isLoading?: boolean;
}

export function NewsForm({ onSubmit, isLoading }: NewsFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<NewsFormData>({
    resolver: zodResolver(newsFormSchema),
    defaultValues: {
      title: '',
      summary: '',
      content: '',
      scope: 'GENERAL',
      coverUrl: '',
    },
  });

  const content = watch('content');

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Title */}
      <div className="space-y-2">
        <Label htmlFor="title">Título *</Label>
        <Input
          id="title"
          {...register('title')}
          placeholder="Escribe el título de la noticia"
          aria-describedby={errors.title ? 'title-error' : undefined}
          aria-invalid={!!errors.title}
        />
        {errors.title && (
          <p id="title-error" className="text-sm text-destructive" role="alert">
            {errors.title.message}
          </p>
        )}
      </div>

      {/* Summary */}
      <div className="space-y-2">
        <Label htmlFor="summary">Resumen</Label>
        <Textarea
          id="summary"
          {...register('summary')}
          placeholder="Breve descripción (opcional)"
          rows={3}
          aria-describedby={errors.summary ? 'summary-error' : undefined}
        />
        {errors.summary && (
          <p id="summary-error" className="text-sm text-destructive" role="alert">
            {errors.summary.message}
          </p>
        )}
      </div>

      {/* Content (Rich Text) */}
      <div className="space-y-2">
        <Label htmlFor="content">Contenido</Label>
        <ReactQuill
          id="content"
          theme="snow"
          value={content || ''}
          onChange={(value) => setValue('content', value)}
          placeholder="Escribe el contenido de la noticia..."
          className="bg-background"
        />
      </div>

      {/* Scope */}
      <div className="space-y-2">
        <Label htmlFor="scope">Ámbito</Label>
        <Select
          defaultValue="GENERAL"
          onValueChange={(value) => setValue('scope', value as 'GENERAL' | 'INTERNAL')}
        >
          <SelectTrigger id="scope">
            <SelectValue placeholder="Selecciona el ámbito" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="GENERAL">General (público)</SelectItem>
            <SelectItem value="INTERNAL">Interno (solo socios)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Submit */}
      <div className="flex justify-end gap-4">
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Guardando...' : 'Guardar Borrador'}
        </Button>
      </div>
    </form>
  );
}
```

---

### Task 5: Create NewsFormPage Component
- **Purpose**: Page wrapper that connects form to API mutation. Presentation layer.
- **Prerequisites**: Task 3, 4
- **Artifacts impacted**: 
  - `frontend/src/features/news/pages/NewsFormPage.tsx`
  - `frontend/src/features/news/pages/index.ts`
- **Test types**: Component (integration)
- **BDD Acceptance**:
  ```
  # Scenario: Successfully create a draft news article
  Given I am on /admin/news/new
  When I fill the form with valid data
  And I click "Guardar Borrador"
  Then I see success message "Noticia guardada como borrador"
  And I am redirected to the news list (or stay on page with success state)
  ```

**Page Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]

import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { NewsForm } from '../components/NewsForm';
import { useCreateNews } from '../api/useCreateNews';
import type { NewsFormData } from '../schemas/news.schema';

export function NewsFormPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const createNews = useCreateNews();

  const handleSubmit = (data: NewsFormData) => {
    createNews.mutate(data, {
      onSuccess: () => {
        toast({
          title: 'Noticia guardada',
          description: 'Noticia guardada como borrador',
        });
        // Navigate to news list or stay on page
        navigate('/admin/news');
      },
      onError: (error) => {
        toast({
          title: 'Error',
          description: 'No se pudo guardar la noticia. Intenta de nuevo.',
          variant: 'destructive',
        });
        console.error('Create news error:', error);
      },
    });
  };

  return (
    <div className="container max-w-3xl py-8">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Crear Noticia</CardTitle>
        </CardHeader>
        <CardContent>
          <NewsForm
            onSubmit={handleSubmit}
            isLoading={createNews.isPending}
          />
        </CardContent>
      </Card>
    </div>
  );
}
```

---

### Task 6: Add Route
- **Purpose**: Register page route in admin section. Wiring step.
- **Prerequisites**: Task 5
- **Artifacts impacted**: 
  - `frontend/src/routes/index.tsx` or equivalent router config
- **Test types**: Manual (navigate to route)
- **BDD Acceptance**:
  ```
  Given I am logged in as Admin
  When I navigate to /admin/news/new
  Then I see the NewsFormPage
  ```

**Route Addition** (example):
```tsx
// In routes config
{
  path: '/admin/news/new',
  element: <NewsFormPage />,
  // Add auth guard if needed
}
```

---

### Task 7: Write Unit Tests
- **Purpose**: TDD validation for Zod schema. Supports `NM-ADMIN-001-FE-T01`.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `frontend/src/features/news/schemas/__tests__/news.schema.test.ts`
- **Test types**: Unit (Vitest)
- **BDD Acceptance**:
  ```
  Given the schema tests exist
  When I run npm run test
  Then all validation tests pass
  ```

**Test Template**:
```typescript
// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]

import { describe, it, expect } from 'vitest';
import { newsFormSchema } from '../news.schema';

describe('newsFormSchema', () => {
  it('validates successfully with minimal data', () => {
    const result = newsFormSchema.safeParse({ title: 'Test Article' });
    expect(result.success).toBe(true);
  });

  it('fails when title is empty', () => {
    const result = newsFormSchema.safeParse({ title: '' });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe('El título es obligatorio');
    }
  });

  it('fails when title exceeds 255 characters', () => {
    const result = newsFormSchema.safeParse({ title: 'a'.repeat(256) });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('255');
    }
  });

  it('accepts optional summary and content', () => {
    const result = newsFormSchema.safeParse({
      title: 'Test',
      summary: null,
      content: null,
    });
    expect(result.success).toBe(true);
  });
});
```

---

### Task 8: Write Component Tests
- **Purpose**: RTL tests for NewsForm component. Supports accessibility validation.
- **Prerequisites**: Tasks 4
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/__tests__/NewsForm.test.tsx`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  Given the component tests exist
  When I run npm run test
  Then all NewsForm tests pass
  And accessibility requirements are verified
  ```

**Test Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { NewsForm } from '../NewsForm';

describe('NewsForm', () => {
  it('renders all form fields', () => {
    render(<NewsForm onSubmit={vi.fn()} />);
    
    expect(screen.getByLabelText(/título/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/resumen/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/ámbito/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /guardar borrador/i })).toBeInTheDocument();
  });

  it('shows validation error when title is empty', async () => {
    const user = userEvent.setup();
    render(<NewsForm onSubmit={vi.fn()} />);
    
    await user.click(screen.getByRole('button', { name: /guardar borrador/i }));
    
    await waitFor(() => {
      expect(screen.getByText('El título es obligatorio')).toBeInTheDocument();
    });
  });

  it('calls onSubmit with valid data', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<NewsForm onSubmit={onSubmit} />);
    
    await user.type(screen.getByLabelText(/título/i), 'Test Article');
    await user.click(screen.getByRole('button', { name: /guardar borrador/i }));
    
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Test Article' })
      );
    });
  });

  it('has proper label associations for accessibility', () => {
    render(<NewsForm onSubmit={vi.fn()} />);
    
    const titleInput = screen.getByLabelText(/título/i);
    expect(titleInput).toHaveAttribute('id', 'title');
  });
});
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Schema Tests | `docker compose exec frontend npm run test -- news.schema.test.ts` | All pass |
| Component Tests | `docker compose exec frontend npm run test -- NewsForm.test.tsx` | All pass |
| All Frontend Tests | `docker compose exec frontend npm run test` | All pass |

### Manual Verification
1. Start frontend: `docker compose up -d frontend`
2. Navigate to: `http://localhost:5188/admin/news/new`
3. Verify:
   - [ ] Page renders with form
   - [ ] Title field has visible label
   - [ ] Rich text editor loads
   - [ ] Scope dropdown works
   - [ ] Empty title shows Spanish error "El título es obligatorio"
   - [ ] Form submits successfully with valid data
   - [ ] Success toast appears
   - [ ] Focus ring is visible on all inputs

### Accessibility Verification
- Run: Browser DevTools > Lighthouse > Accessibility
- Check: Screen reader announces form labels correctly
- Check: Tab order is logical

---

## 6) Dependencies to Add

If not already present in `frontend/package.json`:
```bash
npm install react-quill-new
```

---

## 7) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `frontend/package.json` | MODIFY (add react-quill-new) |
| `frontend/src/index.css` | MODIFY (import Quill CSS) |
| `frontend/src/features/news/schemas/news.schema.ts` | CREATE |
| `frontend/src/features/news/api/useCreateNews.ts` | CREATE |
| `frontend/src/features/news/api/index.ts` | CREATE |
| `frontend/src/features/news/components/NewsForm.tsx` | CREATE |
| `frontend/src/features/news/components/index.ts` | CREATE |
| `frontend/src/features/news/pages/NewsFormPage.tsx` | CREATE |
| `frontend/src/features/news/pages/index.ts` | CREATE |
| `frontend/src/routes/index.tsx` | MODIFY (add route) |
| `frontend/src/features/news/schemas/__tests__/news.schema.test.ts` | CREATE |
| `frontend/src/features/news/components/__tests__/NewsForm.test.tsx` | CREATE |

---

## 8) Brand Compliance Checklist

- [ ] All labels/messages in Spanish (Castilian)
- [ ] Using shadcn/ui components
- [ ] Using semantic tokens (not hex values)
- [ ] Form spacing follows 8pt grid
- [ ] Primary button uses brand color
- [ ] Visible focus rings (2px minimum)
- [ ] Touch targets ≥ 44×44
- [ ] Error messages use `text-destructive` token
