'use server';

import { db, tables } from '@/db';
import { requireTenantContext } from '@/lib/auth';
import { eq, and } from 'drizzle-orm';
import { revalidatePath, revalidateTag } from 'next/cache';
import { emitRealtimeEvent } from '@/lib/realtime';
import { createInterventionSchema, parseFormData } from '@/lib/validation';

export async function createIntervention(formData: FormData) {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) throw new Error('Unauthorized');
  const parsed = parseFormData(createInterventionSchema, formData);

  const [created] = await db
    .insert(tables.interventions)
    .values({
      districtId,
      institutionId,
      studentId: parsed.studentId,
      title: parsed.title,
      interventionType: parsed.interventionType,
      description: parsed.description?.trim() || null,
      priority: parsed.priority?.trim() || 'medium',
      status: parsed.status?.trim() || 'planned',
      assignedTo: parsed.assignedTo?.trim() || null,
      dueDate: parsed.dueDate ? new Date(parsed.dueDate) : null
    })
    .returning();

  revalidatePath('/interventions');
  revalidatePath('/dashboard');
  revalidateTag('dashboard-stats', { expire: 0 });
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/interventions', '/dashboard'],
    districtId,
    institutionId
  });

  return created;
}

export async function updateInterventionStatus(interventionId: number, status: string) {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) throw new Error('Unauthorized');
  const [updated] = await db
    .update(tables.interventions)
    .set({
      status,
      updatedAt: new Date(),
      completedDate: status === 'completed' ? new Date() : null
    })
    .where(
      and(
        eq(tables.interventions.id, interventionId),
        eq(tables.interventions.districtId, districtId),
        eq(tables.interventions.institutionId, institutionId)
      )
    )
    .returning();

  revalidatePath('/interventions');
  revalidatePath('/dashboard');
  revalidateTag('dashboard-stats', { expire: 0 });
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/interventions', '/dashboard'],
    districtId,
    institutionId
  });

  return updated;
}

export async function deleteIntervention(interventionId: number) {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) throw new Error('Unauthorized');
  const [deleted] = await db
    .delete(tables.interventions)
    .where(
      and(
        eq(tables.interventions.id, interventionId),
        eq(tables.interventions.districtId, districtId),
        eq(tables.interventions.institutionId, institutionId)
      )
    )
    .returning();

  revalidatePath('/interventions');
  revalidatePath('/dashboard');
  revalidateTag('dashboard-stats', { expire: 0 });
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/interventions', '/dashboard'],
    districtId,
    institutionId
  });

  return deleted;
}

export async function updateInterventionDetails(
  interventionId: number,
  updates: {
    title?: string;
    interventionType?: string;
    description?: string | null;
    priority?: string | null;
    status?: string | null;
    assignedTo?: string | null;
    dueDate?: string | null;
  }
) {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) throw new Error('Unauthorized');
  const hasStatus = Object.prototype.hasOwnProperty.call(updates, 'status');
  const hasDueDate = Object.prototype.hasOwnProperty.call(updates, 'dueDate');
  const hasDescription = Object.prototype.hasOwnProperty.call(updates, 'description');
  const hasAssignedTo = Object.prototype.hasOwnProperty.call(updates, 'assignedTo');

  const nextStatus = hasStatus ? updates.status ?? null : undefined;
  const parsedDueDate = hasDueDate
    ? updates.dueDate
      ? new Date(updates.dueDate)
      : null
    : undefined;

  const [updated] = await db
    .update(tables.interventions)
    .set({
      title: updates.title?.trim() || undefined,
      interventionType: updates.interventionType?.trim() || undefined,
      description: hasDescription ? updates.description?.trim() || null : undefined,
      priority: updates.priority ?? undefined,
      status: nextStatus,
      assignedTo: hasAssignedTo ? updates.assignedTo?.trim() || null : undefined,
      dueDate: parsedDueDate,
      updatedAt: new Date(),
      completedDate:
        nextStatus === undefined
          ? undefined
          : nextStatus === 'completed'
            ? new Date()
            : null
    })
    .where(
      and(
        eq(tables.interventions.id, interventionId),
        eq(tables.interventions.districtId, districtId),
        eq(tables.interventions.institutionId, institutionId)
      )
    )
    .returning();

  revalidatePath('/interventions');
  revalidatePath('/dashboard');
  revalidateTag('dashboard-stats', { expire: 0 });
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/interventions', '/dashboard'],
    districtId,
    institutionId
  });

  return updated;
}

export type InterventionActionState = {
  status: 'idle' | 'success' | 'error';
  error?: string;
  record?: typeof tables.interventions.$inferSelect;
};

export async function createInterventionAction(
  _prevState: InterventionActionState,
  formData: FormData
): Promise<InterventionActionState> {
  try {
    const record = await createIntervention(formData);
    return { status: 'success', record };
  } catch (error) {
    return {
      status: 'error',
      error: error instanceof Error ? error.message : 'Unexpected error'
    };
  }
}
