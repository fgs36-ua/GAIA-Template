// [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-FE-T01]

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NewsFormPage } from '../NewsFormPage';

// Mock ReactQuill since jsdom cannot handle the canvas/DOM APIs it uses
vi.mock('react-quill-new', () => ({
    default: ({ value, onChange, placeholder, id }: {
        value: string;
        onChange: (val: string) => void;
        placeholder: string;
        id: string;
    }) => (
        <textarea
            data-testid="quill-editor"
            id={id}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
        />
    ),
}));

// Mock sonner toast
vi.mock('sonner', () => ({
    toast: {
        success: vi.fn(),
        error: vi.fn(),
    },
}));

const mockMutate = vi.fn();

// Mock API hooks
vi.mock('../../api/useNewsById', () => ({
    useNewsById: (id: string | undefined) => {
        if (!id) return { data: undefined, isLoading: false, isError: false };
        if (id === 'not-found-id') return { data: undefined, isLoading: false, isError: true };
        if (id === 'loading-id') return { data: undefined, isLoading: true, isError: false };
        return {
            data: {
                id,
                title: 'Existing Title',
                summary: 'Existing summary',
                content: '<p>Existing content</p>',
                scope: 'GENERAL',
                status: 'DRAFT',
                author_id: 'author-1',
                cover_url: null,
                published_at: null,
                created_at: '2026-01-01T00:00:00Z',
                updated_at: '2026-01-01T00:00:00Z',
            },
            isLoading: false,
            isError: false,
        };
    },
}));

vi.mock('../../api/useUpdateNews', () => ({
    useUpdateNews: () => ({
        mutate: mockMutate,
        isPending: false,
    }),
}));

vi.mock('../../api/useCreateNews', () => ({
    useCreateNews: () => ({
        mutate: vi.fn(),
        isPending: false,
    }),
}));

function renderWithRouter(initialRoute: string) {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });

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
}

describe('NewsFormPage - Edit Mode', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('shows "Editar Noticia" title when editing', () => {
        renderWithRouter('/admin/news/123/edit');

        expect(screen.getByText('Editar Noticia')).toBeInTheDocument();
    });

    it('pre-populates form with article data', () => {
        renderWithRouter('/admin/news/123/edit');

        expect(screen.getByDisplayValue('Existing Title')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Existing summary')).toBeInTheDocument();
    });

    it('shows "Guardar Cambios" button in edit mode', () => {
        renderWithRouter('/admin/news/123/edit');

        expect(screen.getByRole('button', { name: /guardar cambios/i })).toBeInTheDocument();
    });

    it('shows "Noticia no encontrada" when article is not found', () => {
        renderWithRouter('/admin/news/not-found-id/edit');

        expect(screen.getByText('Noticia no encontrada')).toBeInTheDocument();
    });

    it('shows loading skeleton while fetching', () => {
        renderWithRouter('/admin/news/loading-id/edit');

        // Skeleton renders div elements with animate-pulse class
        const skeletons = document.querySelectorAll('[data-slot="skeleton"]');
        expect(skeletons.length).toBeGreaterThan(0);
    });

    it('calls update mutation on submit', async () => {
        const user = userEvent.setup();
        renderWithRouter('/admin/news/123/edit');

        const titleInput = screen.getByDisplayValue('Existing Title');
        await user.clear(titleInput);
        await user.type(titleInput, 'Updated Title');

        await user.click(screen.getByRole('button', { name: /guardar cambios/i }));

        await waitFor(() => {
            expect(mockMutate).toHaveBeenCalledWith(
                expect.objectContaining({
                    id: '123',
                    data: expect.objectContaining({ title: 'Updated Title' }),
                }),
                expect.any(Object)
            );
        }, { timeout: 5000 });
    });
});

describe('NewsFormPage - Create Mode', () => {
    it('shows "Crear Noticia" title when creating', () => {
        renderWithRouter('/admin/news/new');

        expect(screen.getByText('Crear Noticia')).toBeInTheDocument();
    });

    it('shows "Guardar Borrador" button in create mode', () => {
        renderWithRouter('/admin/news/new');

        expect(screen.getByRole('button', { name: /guardar borrador/i })).toBeInTheDocument();
    });

    it('form fields are empty in create mode', () => {
        renderWithRouter('/admin/news/new');

        const titleInput = screen.getByLabelText(/título/i) as HTMLInputElement;
        expect(titleInput.value).toBe('');
    });
});
