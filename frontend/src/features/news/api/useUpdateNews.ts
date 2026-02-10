// [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-FE-T01]

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { http } from '@/api/http';

interface UpdateNewsInput {
    title: string;
    summary?: string | null;
    content?: string | null;
    scope: 'GENERAL' | 'INTERNAL';
    coverUrl?: string | null;
}

interface UpdateNewsParams {
    id: string;
    data: UpdateNewsInput;
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
