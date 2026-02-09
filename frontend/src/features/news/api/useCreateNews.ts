// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { http } from '@/api/http';

interface CreateNewsInput {
    title: string;
    summary?: string | null;
    content?: string | null;
    scope: 'GENERAL' | 'INTERNAL';
    coverUrl?: string | null;
}

interface NewsResponse {
    id: string;
    title: string;
    summary: string | null;
    content: string | null;
    status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
    scope: 'GENERAL' | 'INTERNAL';
    author_id: string;
    cover_url: string | null;
    published_at: string | null;
    created_at: string;
    updated_at: string;
}

async function createNews(data: CreateNewsInput): Promise<NewsResponse> {
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
