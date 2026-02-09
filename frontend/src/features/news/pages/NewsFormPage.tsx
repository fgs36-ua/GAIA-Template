// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]

import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { NewsForm } from '../components/NewsForm';
import { useCreateNews } from '../api/useCreateNews';

interface NewsFormValues {
    title: string;
    summary?: string | null;
    content?: string | null;
    scope: 'GENERAL' | 'INTERNAL';
    coverUrl?: string | null;
}

export function NewsFormPage() {
    const navigate = useNavigate();
    const createNews = useCreateNews();

    const handleSubmit = (data: NewsFormValues) => {
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
    };

    return (
        <div className="container max-w-3xl py-8">
            <Card>
                <CardHeader>
                    <CardTitle className="text-2xl">Crear Noticia</CardTitle>
                </CardHeader>
                <CardContent>
                    <NewsForm
                        onSubmit={handleSubmit}
                        isLoading={createNews.isPending}
                    />
                </CardContent>
            </Card>
        </div>
    );
}
