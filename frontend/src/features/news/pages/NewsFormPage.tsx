// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]
// [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-FE-T01]

import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { NewsForm } from '../components/NewsForm';
import { useCreateNews } from '../api/useCreateNews';
import { useUpdateNews } from '../api/useUpdateNews';
import { useNewsById } from '../api/useNewsById';
import type { FormValues } from '../components/NewsForm';

export function NewsFormPage() {
    const navigate = useNavigate();
    const { id } = useParams<{ id: string }>();

    const isEditMode = !!id;

    // [Feature: News Management] [Story: NM-ADMIN-002] [Ticket: NM-ADMIN-002-FE-T01]
    // Fetch existing article for edit mode
    const { data: article, isLoading, isError } = useNewsById(id);

    // Mutations
    const createNews = useCreateNews();
    const updateNews = useUpdateNews();

    const handleSubmit = (data: FormValues) => {
        if (isEditMode && id) {
            updateNews.mutate({ id, data }, {
                onSuccess: () => {
                    toast.success('Cambios guardados');
                    navigate('/admin/news');
                },
                onError: () => {
                    toast.error('No se pudo actualizar la noticia. Intenta de nuevo.');
                },
            });
        } else {
            createNews.mutate(data, {
                onSuccess: () => {
                    toast.success('Noticia guardada como borrador');
                    navigate('/');
                },
                onError: (error: Error) => {
                    toast.error('No se pudo guardar la noticia. Intenta de nuevo.');
                    console.error('Create news error:', error);
                },
            });
        }
    };

    // Error state (404)
    if (isEditMode && isError) {
        return (
            <div className="container max-w-3xl py-8">
                <Card>
                    <CardContent className="py-8 text-center">
                        <p className="text-destructive">Noticia no encontrada</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Loading state
    if (isEditMode && isLoading) {
        return (
            <div className="container max-w-3xl py-8">
                <Card>
                    <CardHeader>
                        <Skeleton className="h-8 w-48" />
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-24 w-full" />
                        <Skeleton className="h-48 w-full" />
                        <Skeleton className="h-10 w-32" />
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Default values for edit mode (map snake_case API response to camelCase form)
    const defaultValues = isEditMode && article ? {
        title: article.title,
        summary: article.summary || '',
        content: article.content || '',
        scope: article.scope,
        coverUrl: article.cover_url || '',
    } : undefined;

    return (
        <div className="container max-w-3xl py-8">
            <Card>
                <CardHeader>
                    <CardTitle className="text-2xl">
                        {isEditMode ? 'Editar Noticia' : 'Crear Noticia'}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <NewsForm
                        onSubmit={handleSubmit}
                        isLoading={createNews.isPending || updateNews.isPending}
                        defaultValues={defaultValues}
                        submitLabel={isEditMode ? 'Guardar Cambios' : 'Guardar Borrador'}
                    />
                </CardContent>
            </Card>
        </div>
    );
}
