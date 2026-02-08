# NM-ADMIN-004-FE-T01 — Implementation Plan

**Source ticket**: `specs/features/news_management/tickets.md` → **NM-ADMIN-004-FE-T01**  
**Related user story**: **NM-ADMIN-004** (from `specs/features/news_management/user-stories.md`)  
**Plan version**: v1.0 — (GAIA, 2026-02-08)  
**Traceability**: All components must include inline references to `NM-ADMIN-004-FE-T01`

---

## 1) Context & Objective

### Ticket Summary
Add archive and restore buttons to article views. Key requirements:
- Archive button visible for PUBLISHED articles only
- Restore button visible for ARCHIVED articles only
- Confirmation dialogs for both actions
- Success toasts after each action
- TanStack Query mutations for API calls

**Business Value**: Administrators can manage article lifecycle directly from the UI with clear feedback.

### Impacted Components
| Component | Type | Operation |
|-----------|------|-----------|
| `useArchiveNews` | API Hook | CREATE |
| `useRestoreNews` | API Hook | CREATE |
| `ArchiveButton` | Component | CREATE |
| `RestoreButton` | Component | CREATE |
| `NewsActionsBar` | Component | CREATE (or extend existing) |

### Impacted BDD Scenarios
This ticket implements the UI for:
- **"Successfully archive an article"** — Click "Archivar", see success toast
- **"Restore an archived article to draft"** — Click "Restaurar a Borrador", see success toast

---

## 2) Scope

### In Scope
- `useArchiveNews` mutation hook (POST /api/news/{id}/archive)
- `useRestoreNews` mutation hook (POST /api/news/{id}/restore)
- `ArchiveButton` component with confirmation dialog
- `RestoreButton` component with confirmation dialog
- Integration in edit view or article actions bar
- Success toasts: "Noticia archivada", "Noticia restaurada a borrador"
- Component tests

### Out of Scope
- Archived list filter (covered in NM-PUBLIC-002)
- Bulk archive/restore
- Undo functionality

### Assumptions
1. **BE-T01 is complete**: Archive/Restore endpoints exist
2. **shadcn/ui AlertDialog**: Available for confirmation
3. **Pattern from FE-T03**: Reuse PublishButton pattern

---

## 3) Detailed Work Plan (TDD + BDD)

### 3.1 Test-First Sequencing

#### Phase 1: RED — Define Tests
1. **Unit tests for hooks**:
   - Test mutation calls correct endpoint
   - Test success callback invalidates queries

2. **Component tests for ArchiveButton**:
   - Test button visible for PUBLISHED status
   - Test button hidden for DRAFT/ARCHIVED status
   - Test confirmation dialog appears
   - Test archive called after confirm

3. **Component tests for RestoreButton**:
   - Test button visible for ARCHIVED status
   - Test button hidden for DRAFT/PUBLISHED status
   - Test confirmation dialog appears
   - Test restore called after confirm

#### Phase 2: GREEN — Minimal Implementation
1. Create mutation hooks
2. Create button components
3. Integrate into NewsFormPage
4. Run tests to verify GREEN state

### 3.2 NFR Hooks

#### Accessibility (A11y)
- Buttons have descriptive aria-labels
- Dialogs follow ARIA dialog pattern

#### UX/Brand
- Spanish labels: "Archivar", "Restaurar a Borrador"
- Consistent with PublishButton pattern

---

## 4) Atomic Task Breakdown

### Task 1: Create useArchiveNews Mutation Hook
- **Purpose**: TanStack Query mutation for POST /api/news/{id}/archive.
- **Prerequisites**: BE-T01 complete
- **Artifacts impacted**: 
  - `frontend/src/features/news/api/useArchiveNews.ts`
  - `frontend/src/features/news/api/index.ts`
- **Test types**: Unit (MSW mock)
- **BDD Acceptance**:
  ```
  Given I call useArchiveNews.mutate(id)
  When the API returns 200
  Then the mutation succeeds
  And the news queries are invalidated
  ```

**Hook Template**:
```typescript
// [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-FE-T01]

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { http } from '@/api/http';

interface ArchiveNewsResponse {
  id: string;
  title: string;
  status: 'ARCHIVED';
}

async function archiveNews(id: string): Promise<ArchiveNewsResponse> {
  const response = await http.post<ArchiveNewsResponse>(`/api/news/${id}/archive`);
  return response.data;
}

export function useArchiveNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: archiveNews,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['news', data.id] });
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });
}
```

---

### Task 2: Create useRestoreNews Mutation Hook
- **Purpose**: TanStack Query mutation for POST /api/news/{id}/restore.
- **Prerequisites**: BE-T01 complete
- **Artifacts impacted**: 
  - `frontend/src/features/news/api/useRestoreNews.ts`
  - `frontend/src/features/news/api/index.ts`
- **Test types**: Unit (MSW mock)
- **BDD Acceptance**:
  ```
  Given I call useRestoreNews.mutate(id)
  When the API returns 200
  Then the mutation succeeds
  And the news queries are invalidated
  ```

**Hook Template**:
```typescript
// [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-FE-T01]

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { http } from '@/api/http';

interface RestoreNewsResponse {
  id: string;
  title: string;
  status: 'DRAFT';
  publishedAt: null;
}

async function restoreNews(id: string): Promise<RestoreNewsResponse> {
  const response = await http.post<RestoreNewsResponse>(`/api/news/${id}/restore`);
  return response.data;
}

export function useRestoreNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: restoreNews,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['news', data.id] });
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });
}
```

---

### Task 3: Create ArchiveButton Component
- **Purpose**: Button with confirmation dialog for archiving. Visible for PUBLISHED only.
- **Prerequisites**: Task 1
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/ArchiveButton.tsx`
  - `frontend/src/features/news/components/index.ts`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  # Scenario: Button visible for PUBLISHED
  Given an article with status "PUBLISHED"
  When I render ArchiveButton
  Then the button is visible
  
  # Scenario: Button hidden for other statuses
  Given an article with status "DRAFT"
  When I render ArchiveButton
  Then the button is not rendered
  
  # Scenario: Confirmation dialog
  Given I click "Archivar"
  Then a confirmation dialog appears
  When I click "Confirmar"
  Then the archive mutation is called
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-FE-T01]

import { useState } from 'react';
import { Archive, Loader2 } from 'lucide-react';
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
import { useArchiveNews } from '../api/useArchiveNews';
import { useToast } from '@/hooks/use-toast';

interface ArchiveButtonProps {
  newsId: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  onSuccess?: () => void;
}

export function ArchiveButton({ newsId, status, onSuccess }: ArchiveButtonProps) {
  const [open, setOpen] = useState(false);
  const { toast } = useToast();
  const archiveNews = useArchiveNews();

  // Only show for PUBLISHED articles
  if (status !== 'PUBLISHED') {
    return null;
  }

  const handleArchive = () => {
    archiveNews.mutate(newsId, {
      onSuccess: () => {
        setOpen(false);
        toast({
          title: 'Noticia archivada',
          description: 'La noticia ya no es visible para los usuarios',
        });
        onSuccess?.();
      },
      onError: (error: any) => {
        setOpen(false);
        const message = error.response?.data?.detail || 'Error al archivar la noticia';
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
        <Button variant="outline" className="gap-2">
          <Archive className="h-4 w-4" />
          Archivar
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Archivar noticia?</AlertDialogTitle>
          <AlertDialogDescription>
            La noticia dejará de ser visible para los usuarios. 
            Podrás restaurarla a borrador más tarde si lo necesitas.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={archiveNews.isPending}>
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction 
            onClick={handleArchive}
            disabled={archiveNews.isPending}
          >
            {archiveNews.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Archivando...
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

### Task 4: Create RestoreButton Component
- **Purpose**: Button with confirmation dialog for restoring. Visible for ARCHIVED only.
- **Prerequisites**: Task 2
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/RestoreButton.tsx`
  - `frontend/src/features/news/components/index.ts`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  # Scenario: Button visible for ARCHIVED
  Given an article with status "ARCHIVED"
  When I render RestoreButton
  Then the button is visible
  
  # Scenario: Button hidden for other statuses
  Given an article with status "PUBLISHED"
  When I render RestoreButton
  Then the button is not rendered
  
  # Scenario: Confirmation and success
  Given I click "Restaurar a Borrador"
  When I confirm in the dialog
  Then the restore mutation is called
  And I see "Noticia restaurada a borrador"
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-FE-T01]

import { useState } from 'react';
import { RotateCcw, Loader2 } from 'lucide-react';
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
import { useRestoreNews } from '../api/useRestoreNews';
import { useToast } from '@/hooks/use-toast';

interface RestoreButtonProps {
  newsId: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  onSuccess?: () => void;
}

export function RestoreButton({ newsId, status, onSuccess }: RestoreButtonProps) {
  const [open, setOpen] = useState(false);
  const { toast } = useToast();
  const restoreNews = useRestoreNews();

  // Only show for ARCHIVED articles
  if (status !== 'ARCHIVED') {
    return null;
  }

  const handleRestore = () => {
    restoreNews.mutate(newsId, {
      onSuccess: () => {
        setOpen(false);
        toast({
          title: 'Noticia restaurada',
          description: 'La noticia ha vuelto a estado borrador',
        });
        onSuccess?.();
      },
      onError: (error: any) => {
        setOpen(false);
        const message = error.response?.data?.detail || 'Error al restaurar la noticia';
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
        <Button variant="outline" className="gap-2">
          <RotateCcw className="h-4 w-4" />
          Restaurar a Borrador
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Restaurar noticia?</AlertDialogTitle>
          <AlertDialogDescription>
            La noticia volverá a estado borrador. 
            Deberás publicarla de nuevo para que sea visible.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={restoreNews.isPending}>
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction 
            onClick={handleRestore}
            disabled={restoreNews.isPending}
          >
            {restoreNews.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Restaurando...
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

### Task 5: Create NewsActionsBar Component
- **Purpose**: Unified action bar with conditional buttons based on article status.
- **Prerequisites**: Tasks 3, 4, PublishButton from FE-T03
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/NewsActionsBar.tsx`
  - `frontend/src/features/news/components/index.ts`
- **Test types**: Component
- **BDD Acceptance**:
  ```
  Given a DRAFT article
  When I render NewsActionsBar
  Then I see PublishButton only
  
  Given a PUBLISHED article
  When I render NewsActionsBar
  Then I see ArchiveButton only
  
  Given an ARCHIVED article
  When I render NewsActionsBar
  Then I see RestoreButton only
  ```

**Component Template**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-FE-T01]

import { PublishButton } from './PublishButton';
import { ArchiveButton } from './ArchiveButton';
import { RestoreButton } from './RestoreButton';

interface NewsActionsBarProps {
  newsId: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  onActionComplete?: () => void;
}

export function NewsActionsBar({ newsId, status, onActionComplete }: NewsActionsBarProps) {
  return (
    <div className="flex gap-2">
      <PublishButton newsId={newsId} status={status} onSuccess={onActionComplete} />
      <ArchiveButton newsId={newsId} status={status} onSuccess={onActionComplete} />
      <RestoreButton newsId={newsId} status={status} onSuccess={onActionComplete} />
    </div>
  );
}
```

---

### Task 6: Integrate NewsActionsBar in NewsFormPage
- **Purpose**: Replace individual button with unified action bar.
- **Prerequisites**: Task 5
- **Artifacts impacted**: 
  - `frontend/src/features/news/pages/NewsFormPage.tsx`
- **Test types**: Component
- **BDD Acceptance**:
  ```
  Given I am editing an article
  When the page renders
  Then I see the appropriate action button(s) for the article status
  ```

**Integration Update**:
```tsx
// In NewsFormPage.tsx, replace PublishButton with NewsActionsBar
// [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-FE-T01]

import { NewsActionsBar } from '../components/NewsActionsBar';

// ... in the component
{isEditMode && article && (
  <div className="flex items-center justify-between">
    <CardTitle className="text-2xl">Editar Noticia</CardTitle>
    <NewsActionsBar 
      newsId={article.id} 
      status={article.status}
      onActionComplete={() => navigate('/admin/news')}
    />
  </div>
)}
```

---

### Task 7: Write Component Tests
- **Purpose**: RTL tests for ArchiveButton and RestoreButton.
- **Prerequisites**: Tasks 3, 4
- **Artifacts impacted**: 
  - `frontend/src/features/news/components/__tests__/ArchiveButton.test.tsx`
  - `frontend/src/features/news/components/__tests__/RestoreButton.test.tsx`
- **Test types**: Component (Vitest + RTL)
- **BDD Acceptance**:
  ```
  When I run npm run test -- ArchiveButton RestoreButton
  Then all tests pass
  ```

**Test Template (ArchiveButton)**:
```tsx
// [Feature: News Management] [Story: NM-ADMIN-004] [Ticket: NM-ADMIN-004-FE-T01]

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ArchiveButton } from '../ArchiveButton';

const mockMutate = vi.fn();
vi.mock('../api/useArchiveNews', () => ({
  useArchiveNews: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

const queryClient = new QueryClient();

const renderComponent = (status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED') => {
  return render(
    <QueryClientProvider client={queryClient}>
      <ArchiveButton newsId="123" status={status} />
    </QueryClientProvider>
  );
};

describe('ArchiveButton', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders button for PUBLISHED status', () => {
    renderComponent('PUBLISHED');
    expect(screen.getByRole('button', { name: /archivar/i })).toBeInTheDocument();
  });

  it('does not render for DRAFT status', () => {
    renderComponent('DRAFT');
    expect(screen.queryByRole('button', { name: /archivar/i })).not.toBeInTheDocument();
  });

  it('does not render for ARCHIVED status', () => {
    renderComponent('ARCHIVED');
    expect(screen.queryByRole('button', { name: /archivar/i })).not.toBeInTheDocument();
  });

  it('shows confirmation dialog on click', async () => {
    const user = userEvent.setup();
    renderComponent('PUBLISHED');
    
    await user.click(screen.getByRole('button', { name: /archivar/i }));
    
    expect(screen.getByText('¿Archivar noticia?')).toBeInTheDocument();
  });

  it('calls mutation on confirm', async () => {
    const user = userEvent.setup();
    renderComponent('PUBLISHED');
    
    await user.click(screen.getByRole('button', { name: /archivar/i }));
    await user.click(screen.getByRole('button', { name: /confirmar/i }));
    
    expect(mockMutate).toHaveBeenCalledWith('123', expect.any(Object));
  });
});
```

---

## 5) Verification Plan

### Automated Tests
| Test Type | Command | Expected Result |
|-----------|---------|-----------------|
| Hook Tests | `docker compose exec frontend npm run test -- useArchiveNews useRestoreNews` | All pass |
| Component Tests | `docker compose exec frontend npm run test -- ArchiveButton RestoreButton` | All pass |
| All Frontend Tests | `docker compose exec frontend npm run test` | All pass |

### Manual Verification
1. Start frontend: `docker compose up -d`
2. Navigate to: `http://localhost:5188/admin/news`
3. **Archive Flow**:
   - Create an article with summary → Publish it
   - Verify "Archivar" button is visible
   - Click → Confirm in dialog
   - Verify toast "Noticia archivada"
   - Verify status changed to ARCHIVED
4. **Restore Flow**:
   - Edit the archived article
   - Verify "Restaurar a Borrador" button is visible
   - Click → Confirm in dialog
   - Verify toast "Noticia restaurada"
   - Verify status changed to DRAFT
5. Verify button visibility rules:
   - DRAFT: Only "Publicar" visible
   - PUBLISHED: Only "Archivar" visible
   - ARCHIVED: Only "Restaurar a Borrador" visible

---

## 6) Files Created/Modified Summary

| File | Operation |
|------|-----------|
| `frontend/src/features/news/api/useArchiveNews.ts` | CREATE |
| `frontend/src/features/news/api/useRestoreNews.ts` | CREATE |
| `frontend/src/features/news/api/index.ts` | MODIFY (export new hooks) |
| `frontend/src/features/news/components/ArchiveButton.tsx` | CREATE |
| `frontend/src/features/news/components/RestoreButton.tsx` | CREATE |
| `frontend/src/features/news/components/NewsActionsBar.tsx` | CREATE |
| `frontend/src/features/news/components/index.ts` | MODIFY (export components) |
| `frontend/src/features/news/pages/NewsFormPage.tsx` | MODIFY (use NewsActionsBar) |
| `frontend/src/features/news/components/__tests__/ArchiveButton.test.tsx` | CREATE |
| `frontend/src/features/news/components/__tests__/RestoreButton.test.tsx` | CREATE |

---

## 7) Brand Compliance Checklist

| Element | Spanish Text |
|---------|--------------|
| Archive button | "Archivar" |
| Archive dialog title | "¿Archivar noticia?" |
| Archive success | "Noticia archivada" |
| Archive loading | "Archivando..." |
| Restore button | "Restaurar a Borrador" |
| Restore dialog title | "¿Restaurar noticia?" |
| Restore success | "Noticia restaurada" |
| Restore loading | "Restaurando..." |
| Cancel | "Cancelar" |
| Confirm | "Confirmar" |

---

## 8) Status-to-Button Matrix

| Article Status | Visible Buttons |
|----------------|-----------------|
| DRAFT | Publicar |
| PUBLISHED | Archivar |
| ARCHIVED | Restaurar a Borrador |
