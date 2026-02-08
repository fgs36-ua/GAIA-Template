# NM-ADMIN-003-FE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-ADMIN-003-FE-T01**  
**Related user story**: **NM-ADMIN-003** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All components must include inline references to `NM-ADMIN-003-FE-T01`

---

## 1) Context & Objective

### Ticket Summary
Add publish button to article detail/edit view. Key requirements:
- Publish button visible for DRAFT articles only
- Confirmation dialog before publishing
- Success toast after publishing
- Error handling for missing summary
- TanStack Query mutation for API call

**Business Value**: Administrators can publish draft articles directly from the UI with a clear workflow and feedback.

### Impacted Components
| Component | Type | Operation |
|-----------|------|-----------|
| `usePublishNews` | API Hook | CREATE |
| `PublishButton` | Component | CREATE |
| `NewsFormPage` or `NewsDetailPage` | Page | MODIFY |

### Impacted BDD Scenarios
This ticket implements the UI for:
- **"Successfully publish an article"** — Click button, see success toast
- **"Cannot publish without summary"** — Show error message

---

## 2) Scope

### In Scope
- `usePublishNews` mutation hook (POST /api/news/{id}/publish)
- `PublishButton` component with confirmation dialog
- Integration in edit view (NewsFormPage)
- Loading indicator during publish
- Success toast: "Noticia publicada"
- Error handling: "El resumen es obligatorio para publicar"
- Component tests

### Out of Scope
- Publish scheduling UI
- Bulk publishing
- Notification to subscribers

### Assumptions
1. **BE-T01 is complete**: POST /api/news/{id}/publish endpoint exists
2. **shadcn/ui AlertDialog**: Available for confirmation
3. **Toast system**: Already configured from previous tickets

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for usePublishNews**:
   - Test mutation calls correct endpoint
   - Test success callback invalidates queries
   - Test error handling

2. **Component tests for PublishButton**:
   - Test button visible for DRAFT status
   - Test button hidden for PUBLISHED status
   - Test confirmation dialog appears on click
   - Test publish called after confirm
   - Test loading state during mutation

#### Phase 2: GREEN — Minimal Implementation
1. Create mutation hook
2. Create PublishButton component
3. Integrate into NewsFormPage
4. Run tests to verify GREEN state

#### Phase 3: REFACTOR
1. Polish loading states
2. Ensure accessibility

### 3.2 NFR Hooks

#### Accessibility (A11y)
- Button has descriptive aria-label
- Dialog follows ARIA dialog pattern
- Focus managed properly

#### UX/Brand
- Spanish labels: "Publicar", "¿Publicar noticia?", "Cancelar", "Confirmar"
- Success: "Noticia publicada"
- shadcn/ui AlertDialog for confirmation

---

## 4) Atomic Task Breakdown

### Task 1: Create usePublishNews Mutation Hook
- **Purpose**: TanStack Query mutation for POST /api/news/{id}/publish.
- **Prerequisites**: BE-T01 complete
- **Artifacts impacted**: 
  - `frontend/src/features/news/api/usePublishNews.ts`
  - `frontend/src/features/news/api/index.ts`
- **Test types**: Unit (MSW mock)
- **BDD Acceptance**:
  ```
  Given I call usePublishNews.mutate(id)
  When the API returns 200
  Then the mutation succeeds
  And the news queries are invalidated
  ```

**Hook Template**:
```typescript
// [Feature: News Management] [Story: NM-ADMIN-003] [Ticket: NM-ADMIN-003-FE-T01]

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { http } from '@/api/http';

interface PublishNewsResponse {
  id: string;
  title: string;
  status: 'PUBLISHED';
  publishedAt: string;
  // ... other fields
}

async function publishNews(id: string): Promise<PublishNewsResponse> {
  const response = await http.post<PublishNewsResponse>(`/api/news/${id}/publish`);
  return response.data;
}

export function usePublishNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: publishNews,
    onSuccess: (data) => {
      // Invalidate specific article and list
      queryClient.invalidateQueries({ queryKey: ['news', data.id] });
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });
}
```

---

### Task 2: Create PublishButton Component
- **Purpose**: Reusable button with confirmation dialog. Core UI deliverable.
- **Prerequisites**: Task 1
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/PublishButton.tsx`
  - `frontend/src/features/news/components/index.ts`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  # Scenario: Button visible for DRAFT
  Given an article with status "DRAFT"
  When I render PublishButton
  Then the button is visible
  
  # Scenario: Button hidden for PUBLISHED
  Given an article with status "PUBLISHED"
  When I render PublishButton
  Then the button is not rendered
  
  # Scenario: Confirmation dialog
  Given I see the publish button
  When I click it
  Then a confirmation dialog appears
  And it asks "¿Publicar noticia?"
  
  # Scenario: Confirm publish
  Given the confirmation dialog is open
  When I click "Confirmar"
  Then the publish mutation is called
  And I see loading state
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-003] [Ticket: NM-ADMIN-003-FE-T01]

import { useState } from 'react';
import { Loader2, Send } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { usePublishNews } from '../api/usePublishNews';
import { useToast } from '@/hooks/use-toast';

interface PublishButtonProps {
  newsId: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  onSuccess?: () => void;
}

export function PublishButton({ newsId, status, onSuccess }: PublishButtonProps) {
  const [open, setOpen] = useState(false);
  const { toast } = useToast();
  const publishNews = usePublishNews();

  // Only show for DRAFT articles
  if (status !== 'DRAFT') {
    return null;
  }

  const handlePublish = () => {
    publishNews.mutate(newsId, {
      onSuccess: () => {
        setOpen(false);
        toast({
          title: 'Noticia publicada',
          description: 'La noticia ya está visible para los usuarios',
        });
        onSuccess?.();
      },
      onError: (error: any) => {
        setOpen(false);
        const message = error.response?.data?.detail || 'Error al publicar la noticia';
        toast({
          title: 'Error',
          description: message,
          variant: 'destructive',
        });
      },
    });
  };

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        <Button variant="default" className="gap-2">
          <Send className="h-4 w-4" />
          Publicar
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Publicar noticia?</AlertDialogTitle>
          <AlertDialogDescription>
            Una vez publicada, la noticia será visible para los usuarios 
            según su ámbito de visibilidad.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={publishNews.isPending}>
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction 
            onClick={handlePublish}
            disabled={publishNews.isPending}
          >
            {publishNews.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Publicando...
              </>
            ) : (
              'Confirmar'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

---

### Task 3: Integrate PublishButton in NewsFormPage
- **Purpose**: Add publish button to edit mode header. Integration step.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `frontend/src/features/news/pages/NewsFormPage.tsx`
- **Test types**: Component
- **BDD Acceptance**:
  ```
  Given I am editing a DRAFT article
  When the page renders
  Then I see the Publish button next to the form title
  
  Given I am editing a PUBLISHED article
  When the page renders
  Then I do NOT see the Publish button
  ```

**Integration Template**:
```tsx
// In NewsFormPage.tsx header area
// [Feature: News Management] [Story: NM-ADMIN-003] [Ticket: NM-ADMIN-003-FE-T01]

import { PublishButton } from '../components/PublishButton';

// ... in the component
{isEditMode && article && (
  <div className="flex items-center justify-between">
    <CardTitle className="text-2xl">Editar Noticia</CardTitle>
    <PublishButton 
      newsId={article.id} 
      status={article.status}
      onSuccess={() => navigate('/admin/news')}
    />
  </div>
)}
```

---

### Task 4: Handle Error Display
- **Purpose**: Show proper error for missing summary scenario.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/PublishButton.tsx` (already handled in Task 2)
- **Test types**: Component
- **BDD Acceptance**:
  ```
  # Scenario: Cannot publish without summary
  Given I try to publish an article without summary
  When the API returns 400
  Then I see error toast "El resumen es obligatorio para publicar"
  ```

> **Note**: Error handling is already implemented in Task 2. This task is verification that the API error message is correctly displayed.

---

### Task 5: Write Component Tests
- **Purpose**: RTL tests for PublishButton. Supports BDD scenarios.
- **Prerequisites**: Tasks 2, 3
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/__tests__/PublishButton.test.tsx`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  Given the component tests exist
  When I run npm run test -- PublishButton
  Then all tests pass
  ```

**Test Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-003] [Ticket: NM-ADMIN-003-FE-T01]

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PublishButton } from '../PublishButton';

// Mock the mutation hook
const mockMutate = vi.fn();
vi.mock('../api/usePublishNews', () => ({
  usePublishNews: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}));

// Mock toast
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

const queryClient = new QueryClient();

const renderComponent = (status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED') => {
  return render(
    <QueryClientProvider client={queryClient}>
      <PublishButton newsId="123" status={status} />
    </QueryClientProvider>
  );
};

describe('PublishButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders button for DRAFT status', () => {
    renderComponent('DRAFT');
    expect(screen.getByRole('button', { name: /publicar/i })).toBeInTheDocument();
  });

  it('does not render for PUBLISHED status', () => {
    renderComponent('PUBLISHED');
    expect(screen.queryByRole('button', { name: /publicar/i })).not.toBeInTheDocument();
  });

  it('does not render for ARCHIVED status', () => {
    renderComponent('ARCHIVED');
    expect(screen.queryByRole('button', { name: /publicar/i })).not.toBeInTheDocument();
  });

  it('shows confirmation dialog on click', async () => {
    const user = userEvent.setup();
    renderComponent('DRAFT');
    
    await user.click(screen.getByRole('button', { name: /publicar/i }));
    
    expect(screen.getByText('¿Publicar noticia?')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /confirmar/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument();
  });

  it('calls mutation on confirm', async () => {
    const user = userEvent.setup();
    renderComponent('DRAFT');
    
    await user.click(screen.getByRole('button', { name: /publicar/i }));
    await user.click(screen.getByRole('button', { name: /confirmar/i }));
    
    expect(mockMutate).toHaveBeenCalledWith('123', expect.any(Object));
  });

  it('closes dialog on cancel', async () => {
    const user = userEvent.setup();
    renderComponent('DRAFT');
    
    await user.click(screen.getByRole('button', { name: /publicar/i }));
    await user.click(screen.getByRole('button', { name: /cancelar/i }));
    
    await waitFor(() => {
      expect(screen.queryByText('¿Publicar noticia?')).not.toBeInTheDocument();
    });
    expect(mockMutate).not.toHaveBeenCalled();
  });
});
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Hook Tests | `docker compose exec frontend npm run test -- usePublishNews.test.ts` | All pass |
| Component Tests | `docker compose exec frontend npm run test -- PublishButton.test.tsx` | All pass |
| All Frontend Tests | `docker compose exec frontend npm run test` | All pass |

### Manual Verification
1. Start frontend: `docker compose up -d`
2. Navigate to: `http://localhost:5188/admin/news`
3. Create a new article WITH a summary (save as draft)
4. Navigate to edit the draft article
5. Verify:
   - [ ] "Publicar" button is visible
   - [ ] Click shows confirmation dialog "¿Publicar noticia?"
   - [ ] "Cancelar" closes dialog without action
   - [ ] "Confirmar" shows loading state
   - [ ] Success shows toast "Noticia publicada"
   - [ ] Button disappears after successful publish
6. Create a new article WITHOUT a summary
7. Try to publish:
   - [ ] Error toast shows "El resumen es obligatorio para publicar"
8. Navigate to a published article:
   - [ ] Verify "Publicar" button is NOT visible

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `frontend/src/features/news/api/usePublishNews.ts` | CREATE |
| `frontend/src/features/news/api/index.ts` | MODIFY (export new hook) |
| `frontend/src/features/news/components/PublishButton.tsx` | CREATE |
| `frontend/src/features/news/components/index.ts` | MODIFY (export component) |
| `frontend/src/features/news/pages/NewsFormPage.tsx` | MODIFY (add PublishButton) |
| `frontend/src/features/news/components/__tests__/PublishButton.test.tsx` | CREATE |

---

## 7) Brand Compliance Checklist

- [ ] Button label: "Publicar" (Spanish)
- [ ] Dialog title: "¿Publicar noticia?" (Spanish)
- [ ] Dialog description: Spanish explanation
- [ ] Cancel button: "Cancelar" (Spanish)
- [ ] Confirm button: "Confirmar" (Spanish)
- [ ] Loading: "Publicando..." (Spanish)
- [ ] Success toast: "Noticia publicada" (Spanish)
- [ ] Icon: Send from Lucide (consistent)
- [ ] Uses shadcn/ui AlertDialog component
