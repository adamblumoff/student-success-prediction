import { z } from 'zod';

export const createInterventionSchema = z.object({
  studentId: z.coerce.number().int().positive(),
  title: z.string().trim().min(1),
  interventionType: z.string().trim().min(1),
  description: z.string().trim().optional().nullable(),
  priority: z.string().trim().optional().nullable(),
  status: z.string().trim().optional().nullable(),
  assignedTo: z.string().trim().optional().nullable(),
  dueDate: z.string().trim().optional().nullable()
});

export const updateTenantSettingsSchema = z.object({
  districtName: z.string().trim().min(1)
});

export const createInstitutionSchema = z.object({
  name: z.string().trim().min(1),
  code: z.string().trim().min(1),
  type: z.string().trim().min(1).default('K12')
});

export const updateInstitutionSchema = z.object({
  institutionId: z.coerce.number().int().positive(),
  name: z.string().trim().min(1),
  code: z.string().trim().min(1),
  type: z.string().trim().min(1).default('K12')
});

export const setActiveInstitutionSchema = z.object({
  institutionId: z.coerce.number().int().positive()
});

export const deleteStudentsSchema = z.object({
  studentIds: z.array(z.coerce.number().int().positive())
});

export const assignCounselorSchema = z.object({
  studentIds: z.array(z.coerce.number().int().positive()),
  counselor: z.string().trim().min(1)
});

export function parseFormData<T extends z.ZodTypeAny>(schema: T, formData: FormData) {
  const data = Object.fromEntries(formData.entries());
  return schema.parse(data) as z.infer<T>;
}
