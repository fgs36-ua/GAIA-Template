// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { NewsForm } from '../NewsForm';

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

describe('NewsForm', () => {
    it('renders all form fields', () => {
        render(<NewsForm onSubmit={vi.fn()} />);

        expect(screen.getByLabelText(/título/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/resumen/i)).toBeInTheDocument();
        expect(screen.getByTestId('quill-editor')).toBeInTheDocument();
        expect(screen.getByLabelText(/ámbito/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /guardar borrador/i })).toBeInTheDocument();
    });

    it('shows validation error when title is empty and form is submitted', async () => {
        const user = userEvent.setup();
        const onSubmit = vi.fn();
        render(<NewsForm onSubmit={onSubmit} />);

        await user.click(screen.getByRole('button', { name: /guardar borrador/i }));

        await waitFor(() => {
            expect(screen.getByText('El título es obligatorio')).toBeInTheDocument();
        });

        expect(onSubmit).not.toHaveBeenCalled();
    });

    it('calls onSubmit with valid data when form is submitted', async () => {
        const user = userEvent.setup();
        const onSubmit = vi.fn();
        render(<NewsForm onSubmit={onSubmit} />);

        await user.type(screen.getByLabelText(/título/i), 'Mi primera noticia');
        await user.click(screen.getByRole('button', { name: /guardar borrador/i }));

        await waitFor(() => {
            expect(onSubmit).toHaveBeenCalledWith(
                expect.objectContaining({ title: 'Mi primera noticia' })
            );
        }, { timeout: 5000 });
    });

    it('has proper label associations for accessibility', () => {
        render(<NewsForm onSubmit={vi.fn()} />);

        const titleInput = screen.getByLabelText(/título/i);
        expect(titleInput).toHaveAttribute('id', 'title');

        const summaryInput = screen.getByLabelText(/resumen/i);
        expect(summaryInput).toHaveAttribute('id', 'summary');
    });

    it('shows loading state on submit button when isLoading is true', () => {
        render(<NewsForm onSubmit={vi.fn()} isLoading />);

        const button = screen.getByRole('button', { name: /guardando/i });
        expect(button).toBeDisabled();
    });

    it('error message is associated with input via aria-describedby', async () => {
        const user = userEvent.setup();
        render(<NewsForm onSubmit={vi.fn()} />);

        await user.click(screen.getByRole('button', { name: /guardar borrador/i }));

        await waitFor(() => {
            const titleInput = screen.getByLabelText(/título/i);
            expect(titleInput).toHaveAttribute('aria-describedby', 'title-error');
            expect(titleInput).toHaveAttribute('aria-invalid', 'true');

            const errorEl = screen.getByText('El título es obligatorio');
            expect(errorEl).toHaveAttribute('id', 'title-error');
            expect(errorEl).toHaveAttribute('role', 'alert');
        });
    });
});
