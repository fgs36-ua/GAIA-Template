// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]

import { z } from 'zod';

export const NewsScope = {
    GENERAL: 'GENERAL',
    INTERNAL: 'INTERNAL',
} as const;

export const newsFormSchema = z.object({
    title: z
        .string()
        .min(1, 'El título es obligatorio')
        .max(255, 'El título no puede exceder 255 caracteres'),
    summary: z
        .string()
        .max(500, 'El resumen no puede exceder 500 caracteres')
        .optional()
        .nullable(),
    content: z.string().optional().nullable(),
    scope: z.enum(['GENERAL', 'INTERNAL']).default('GENERAL'),
    coverUrl: z
        .string()
        .transform((val) => val === '' ? null : val)
        .pipe(
            z.string()
                .url('La URL de portada no es válida')
                .max(2048)
                .nullable()
        )
        .optional()
        .nullable(),
});

export type NewsFormData = z.infer<typeof newsFormSchema>;
