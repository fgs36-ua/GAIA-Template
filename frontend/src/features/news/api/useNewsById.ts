// [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-FE-T01]

import { useQuery } from '@tanstack/react-query';
import { http } from '@/api/http';

export interface NewsArticle {
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
