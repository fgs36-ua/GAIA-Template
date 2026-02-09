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
            const titleError = result.error.issues.find(
                (issue) => issue.path.includes('title')
            );
            expect(titleError?.message).toBe('El título es obligatorio');
        }
    });

    it('fails when title is missing', () => {
        const result = newsFormSchema.safeParse({});
        expect(result.success).toBe(false);
    });

    it('fails when title exceeds 255 characters', () => {
        const result = newsFormSchema.safeParse({ title: 'a'.repeat(256) });
        expect(result.success).toBe(false);
        if (!result.success) {
            const titleError = result.error.issues.find(
                (issue) => issue.path.includes('title')
            );
            expect(titleError?.message).toContain('255');
        }
    });

    it('accepts optional summary and content as null', () => {
        const result = newsFormSchema.safeParse({
            title: 'Test',
            summary: null,
            content: null,
        });
        expect(result.success).toBe(true);
    });

    it('accepts optional summary and content as undefined', () => {
        const result = newsFormSchema.safeParse({
            title: 'Test',
        });
        expect(result.success).toBe(true);
    });

    it('fails when summary exceeds 500 characters', () => {
        const result = newsFormSchema.safeParse({
            title: 'Test',
            summary: 'a'.repeat(501),
        });
        expect(result.success).toBe(false);
        if (!result.success) {
            const summaryError = result.error.issues.find(
                (issue) => issue.path.includes('summary')
            );
            expect(summaryError?.message).toContain('500');
        }
    });

    it('defaults scope to GENERAL when not provided', () => {
        const result = newsFormSchema.safeParse({ title: 'Test' });
        expect(result.success).toBe(true);
        if (result.success) {
            expect(result.data.scope).toBe('GENERAL');
        }
    });

    it('accepts INTERNAL scope', () => {
        const result = newsFormSchema.safeParse({
            title: 'Test',
            scope: 'INTERNAL',
        });
        expect(result.success).toBe(true);
    });

    it('rejects invalid scope value', () => {
        const result = newsFormSchema.safeParse({
            title: 'Test',
            scope: 'INVALID',
        });
        expect(result.success).toBe(false);
    });

    it('rejects invalid coverUrl format', () => {
        const result = newsFormSchema.safeParse({
            title: 'Test',
            coverUrl: 'not-a-url',
        });
        expect(result.success).toBe(false);
        if (!result.success) {
            const urlError = result.error.issues.find(
                (issue) => issue.path.includes('coverUrl')
            );
            expect(urlError?.message).toContain('URL');
        }
    });

    it('accepts valid coverUrl', () => {
        const result = newsFormSchema.safeParse({
            title: 'Test',
            coverUrl: 'https://example.com/cover.jpg',
        });
        expect(result.success).toBe(true);
    });
});
