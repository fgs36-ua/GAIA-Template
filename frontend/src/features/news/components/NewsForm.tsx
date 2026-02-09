// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]

import { useForm, type SubmitHandler, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import ReactQuill from 'react-quill-new';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { newsFormSchema } from '../schemas/news.schema';

// Explicit form values type (avoids Zod v4 inference issues with react-hook-form)
export interface FormValues {
    title: string;
    summary?: string | null;
    content?: string | null;
    scope: 'GENERAL' | 'INTERNAL';
    coverUrl?: string | null;
}

interface NewsFormProps {
    onSubmit: (data: FormValues) => void;
    isLoading?: boolean;
}

export function NewsForm({ onSubmit, isLoading }: NewsFormProps) {
    const {
        register,
        handleSubmit,
        setValue,
        watch,
        formState: { errors },
    } = useForm<FormValues>({
        resolver: zodResolver(newsFormSchema) as Resolver<FormValues>,
        defaultValues: {
            title: '',
            summary: '',
            content: '',
            scope: 'GENERAL',
            coverUrl: '',
        },
    });

    const content = watch('content');

    const onFormSubmit: SubmitHandler<FormValues> = (data) => {
        onSubmit(data);
    };

    return (
        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
            {/* Title */}
            <div className="space-y-2">
                <Label htmlFor="title">Título *</Label>
                <Input
                    id="title"
                    {...register('title')}
                    placeholder="Escribe el título de la noticia"
                    aria-describedby={errors.title ? 'title-error' : undefined}
                    aria-invalid={!!errors.title}
                />
                {errors.title && (
                    <p id="title-error" className="text-sm text-destructive" role="alert">
                        {errors.title.message}
                    </p>
                )}
            </div>

            {/* Summary */}
            <div className="space-y-2">
                <Label htmlFor="summary">Resumen</Label>
                <Textarea
                    id="summary"
                    {...register('summary')}
                    placeholder="Breve descripción (opcional)"
                    rows={3}
                    aria-describedby={errors.summary ? 'summary-error' : undefined}
                />
                {errors.summary && (
                    <p id="summary-error" className="text-sm text-destructive" role="alert">
                        {errors.summary.message}
                    </p>
                )}
            </div>

            {/* Content (Rich Text) */}
            <div className="space-y-2">
                <Label htmlFor="content">Contenido</Label>
                <ReactQuill
                    id="content"
                    theme="snow"
                    value={content || ''}
                    onChange={(value: string) => setValue('content', value)}
                    placeholder="Escribe el contenido de la noticia..."
                    className="bg-background"
                />
            </div>

            {/* Scope */}
            <div className="space-y-2">
                <Label htmlFor="scope">Ámbito</Label>
                <Select
                    defaultValue="GENERAL"
                    onValueChange={(value) => setValue('scope', value as 'GENERAL' | 'INTERNAL')}
                >
                    <SelectTrigger id="scope">
                        <SelectValue placeholder="Selecciona el ámbito" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="GENERAL">General (público)</SelectItem>
                        <SelectItem value="INTERNAL">Interno (solo socios)</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Submit */}
            <div className="flex justify-end gap-4">
                <Button type="submit" disabled={isLoading}>
                    {isLoading ? 'Guardando...' : 'Guardar Borrador'}
                </Button>
            </div>
        </form>
    );
}
