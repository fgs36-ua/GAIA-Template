# NM-ADMIN-005-FE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-ADMIN-005-FE-T01**  
**Related user story**: **NM-ADMIN-005** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All components must include inline references to `NM-ADMIN-005-FE-T01`

---

## 1) Context & Objective

### Ticket Summary
Add delete button with confirmation dialog for news articles. Key requirements:
- Delete button visible for all articles (any status)
- AlertDialog confirmation before deletion
- Calls DELETE API, shows success toast
- Navigates back to list after deletion

**Business Value**: Administrators can remove obsolete content with safety confirmation to prevent accidental deletions.

### Impacted Components
| Component | Type | Operation |
|-----------|------|-----------|
| `useDeleteNews` | API Hook | CREATE |
| `DeleteButton` | Component | CREATE |
| `NewsActionsBar` | Component | MODIFY (add DeleteButton) |

### Impacted BDD Scenarios
This ticket implements:
- **"Successfully soft-delete an article"** — Click "Eliminar", confirm, see success
- **"Cancel deletion dialog"** — Click "Cancelar", article not deleted

---

## 2) Scope

### In Scope
- `useDeleteNews` mutation hook (DELETE /api/news/{id})
- `DeleteButton` component with AlertDialog confirmation
- Integration in NewsActionsBar (visible for all statuses)
- Success toast: "Noticia eliminada"
- Navigation to list after successful deletion
- Component tests

### Out of Scope
- Bulk delete
- Undo functionality
- Hard delete

### Assumptions
1. **BE-T01 is complete**: DELETE endpoint exists
2. **shadcn/ui AlertDialog**: Available for confirmation
3. **NewsActionsBar exists**: From FE-T01 (archive/restore)

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for useDeleteNews hook**:
   - Test mutation calls correct endpoint
   - Test success callback

2. **Component tests for DeleteButton**:
   - Test button always visible (any status)
   - Test confirmation dialog appears
   - Test cancel closes dialog without deletion
   - Test confirm calls mutation

#### Phase 2: GREEN — Minimal Implementation
1. Create mutation hook
2. Create DeleteButton component
3. Integrate into NewsActionsBar
4. Run tests to verify GREEN state

### 3.2 NFR Hooks

#### Accessibility (A11y)
- Destructive action uses variant="destructive"
- Dialog has proper focus management

#### UX/Brand
- Button label: "Eliminar"
- Warning styling (red/destructive)
- Clear confirmation message

---

## 4) Atomic Task Breakdown

### Task 1: Create useDeleteNews Mutation Hook
- **Purpose**: TanStack Query mutation for DELETE /api/news/{id}.
- **Prerequisites**: BE-T01 complete
- **Artifacts impacted**: 
  - `frontend/src/features/news/api/useDeleteNews.ts`
  - `frontend/src/features/news/api/index.ts`
- **Test types**: Unit (MSW mock)
- **BDD Acceptance**:
  ```
  Given I call useDeleteNews.mutate(id)
  When the API returns 204
  Then the mutation succeeds
  And the news queries are invalidated
  ```

**Hook Template**:
```typescript
// [Feature: News Management] [Story: NM-ADMIN-005] [Ticket: NM-ADMIN-005-FE-T01]

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { http } from '@/api/http';

async function deleteNews(id: string): Promise<void> {
  await http.delete(`/api/news/${id}`);
}

export function useDeleteNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteNews,
    onSuccess: () => {
      // Invalidate all news queries since a news item was deleted
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });
}
```

---

### Task 2: Create DeleteButton Component
- **Purpose**: Delete button with destructive confirmation dialog.
- **Prerequisites**: Task 1
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/DeleteButton.tsx`
  - `frontend/src/features/news/components/index.ts`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  # Scenario: Always visible
  Given an article with any status
  When I render DeleteButton
  Then the button is visible
  
  # Scenario: Cancel dialog
  Given I click "Eliminar"
  When I click "Cancelar"
  Then the dialog closes
  And the article is not deleted
  
  # Scenario: Confirm deletion
  Given I click "Eliminar"
  When I click "Sí, eliminar"
  Then the delete mutation is called
  And I see "Noticia eliminada"
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-005] [Ticket: NM-ADMIN-005-FE-T01]

import { useState } from 'react';
import { Trash2, Loader2 } from 'lucide-react';
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
import { useDeleteNews } from '../api/useDeleteNews';
import { useToast } from '@/hooks/use-toast';

interface DeleteButtonProps {
  newsId: string;
  newsTitle: string;
  onSuccess?: () => void;
}

export function DeleteButton({ newsId, newsTitle, onSuccess }: DeleteButtonProps) {
  const [open, setOpen] = useState(false);
  const { toast } = useToast();
  const deleteNews = useDeleteNews();

  const handleDelete = () => {
    deleteNews.mutate(newsId, {
      onSuccess: () => {
        setOpen(false);
        toast({
          title: 'Noticia eliminada',
          description: `"${newsTitle}" ha sido eliminada`,
        });
        onSuccess?.();
      },
      onError: (error: any) => {
        setOpen(false);
        const message = error.response?.data?.detail || 'Error al eliminar la noticia';
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
        <Button variant="destructive" className="gap-2">
          <Trash2 className="h-4 w-4" />
          Eliminar
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Eliminar noticia?</AlertDialogTitle>
          <AlertDialogDescription>
            Esta acción no se puede deshacer. La noticia "{newsTitle}" 
            será eliminada permanentemente.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteNews.isPending}>
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction 
            onClick={handleDelete}
            disabled={deleteNews.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {deleteNews.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Eliminando...
              </>
            ) : (
              'Sí, eliminar'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

---

### Task 3: Update NewsActionsBar to Include DeleteButton
- **Purpose**: Add DeleteButton to unified action bar.
- **Prerequisites**: Task 2, NewsActionsBar from FE-T01
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/NewsActionsBar.tsx`
- **Test types**: Component
- **BDD Acceptance**:
  ```
  Given any article
  When I render NewsActionsBar
  Then I see the delete button alongside other actions
  ```

**Updated Component**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-005] [Ticket: NM-ADMIN-005-FE-T01]

import { PublishButton } from './PublishButton';
import { ArchiveButton } from './ArchiveButton';
import { RestoreButton } from './RestoreButton';
import { DeleteButton } from './DeleteButton';

interface NewsActionsBarProps {
  newsId: string;
  newsTitle: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  onActionComplete?: () => void;
}

export function NewsActionsBar({ 
  newsId, 
  newsTitle,
  status, 
  onActionComplete 
}: NewsActionsBarProps) {
  return (
    <div className="flex gap-2">
      {/* Status-dependent buttons */}
      <PublishButton newsId={newsId} status={status} onSuccess={onActionComplete} />
      <ArchiveButton newsId={newsId} status={status} onSuccess={onActionComplete} />
      <RestoreButton newsId={newsId} status={status} onSuccess={onActionComplete} />
      
      {/* Delete is always available */}
      <DeleteButton 
        newsId={newsId} 
        newsTitle={newsTitle} 
        onSuccess={onActionComplete} 
      />
    </div>
  );
}
```

---

### Task 4: Update NewsFormPage Integration
- **Purpose**: Pass newsTitle to NewsActionsBar for delete confirmation.
- **Prerequisites**: Task 3
- **Artifacts impacted**: 
  - `frontend/src/features/news/pages/NewsFormPage.tsx`
- **Test types**: Component
- **BDD Acceptance**:
  ```
  Given I am editing an article
  When delete is successful
  Then I am navigated to the news list
  ```

**Integration Update**:
```tsx
// In NewsFormPage.tsx
// [Feature: News Management] [Story: NM-ADMIN-005] [Ticket: NM-ADMIN-005-FE-T01]

{isEditMode && article && (
  <div className="flex items-center justify-between">
    <CardTitle className="text-2xl">Editar Noticia</CardTitle>
    <NewsActionsBar 
      newsId={article.id} 
      newsTitle={article.title}
      status={article.status}
      onActionComplete={() => navigate('/admin/news')}
    />
  </div>
)}
```

---

### Task 5: Write Component Tests
- **Purpose**: RTL tests for DeleteButton.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/__tests__/DeleteButton.test.tsx`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  When I run npm run test -- DeleteButton
  Then all tests pass
  ```

**Test Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-005] [Ticket: NM-ADMIN-005-FE-T01]

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DeleteButton } from '../DeleteButton';

const mockMutate = vi.fn();
vi.mock('../api/useDeleteNews', () => ({
  useDeleteNews: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

const queryClient = new QueryClient();

const renderComponent = () => {
  return render(
    <QueryClientProvider client={queryClient}>
      <DeleteButton newsId="123" newsTitle="Test Article" />
    </QueryClientProvider>
  );
};

describe('DeleteButton', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders delete button', () => {
    renderComponent();
    expect(screen.getByRole('button', { name: /eliminar/i })).toBeInTheDocument();
  });

  it('shows confirmation dialog on click', async () => {
    const user = userEvent.setup();
    renderComponent();
    
    await user.click(screen.getByRole('button', { name: /eliminar/i }));
    
    expect(screen.getByText('¿Eliminar noticia?')).toBeInTheDocument();
    expect(screen.getByText(/Test Article/)).toBeInTheDocument();
  });

  it('closes dialog on cancel', async () => {
    const user = userEvent.setup();
    renderComponent();
    
    await user.click(screen.getByRole('button', { name: /eliminar/i }));
    await user.click(screen.getByRole('button', { name: /cancelar/i }));
    
    await waitFor(() => {
      expect(screen.queryByText('¿Eliminar noticia?')).not.toBeInTheDocument();
    });
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it('calls mutation on confirm', async () => {
    const user = userEvent.setup();
    renderComponent();
    
    await user.click(screen.getByRole('button', { name: /eliminar/i }));
    await user.click(screen.getByRole('button', { name: /sí, eliminar/i }));
    
    expect(mockMutate).toHaveBeenCalledWith('123', expect.any(Object));
  });
});
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Hook Tests | `docker compose exec frontend npm run test -- useDeleteNews` | All pass |
| Component Tests | `docker compose exec frontend npm run test -- DeleteButton` | All pass |
| All Frontend Tests | `docker compose exec frontend npm run test` | All pass |

### Manual Verification
1. Start frontend: `docker compose up -d`
2. Navigate to: `http://localhost:5188/admin/news`
3. **Delete Flow**:
   - Create a test article
   - Click "Eliminar"
   - Verify confirmation dialog appears with article title
   - Click "Cancelar" → Dialog closes, article still exists
   - Click "Eliminar" again
   - Click "Sí, eliminar"
   - Verify toast "Noticia eliminada"
   - Verify navigation to news list
   - Verify article no longer in list
4. Verify delete button visible for all statuses:
   - DRAFT → Delete button visible
   - PUBLISHED → Delete button visible
   - ARCHIVED → Delete button visible

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `frontend/src/features/news/api/useDeleteNews.ts` | CREATE |
| `frontend/src/features/news/api/index.ts` | MODIFY (export new hook) |
| `frontend/src/features/news/components/DeleteButton.tsx` | CREATE |
| `frontend/src/features/news/components/NewsActionsBar.tsx` | MODIFY (add DeleteButton) |
| `frontend/src/features/news/components/index.ts` | MODIFY (export DeleteButton) |
| `frontend/src/features/news/pages/NewsFormPage.tsx` | MODIFY (pass newsTitle) |
| `frontend/src/features/news/components/__tests__/DeleteButton.test.tsx` | CREATE |

---

## 7) Brand Compliance Checklist

| Element | Spanish Text |
|---------|--------------|
| Delete button | "Eliminar" |
| Dialog title | "¿Eliminar noticia?" |
| Dialog description | "Esta acción no se puede deshacer. La noticia "{title}" será eliminada permanentemente." |
| Cancel button | "Cancelar" |
| Confirm button | "Sí, eliminar" |
| Loading state | "Eliminando..." |
| Success toast | "Noticia eliminada" |
| Error toast | "Error al eliminar la noticia" |

---

## 8) Final NewsActionsBar Button Matrix

| Article Status | Visible Buttons |
|----------------|-----------------|
| DRAFT | Publicar, **Eliminar** |
| PUBLISHED | Archivar, **Eliminar** |
| ARCHIVED | Restaurar a Borrador, **Eliminar** |

> **Note**: Delete button is always visible regardless of status.
