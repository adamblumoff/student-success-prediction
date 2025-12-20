'use server';

import { auth } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { getInstitutionId } from '@/lib/auth';
import { eq, and } from 'drizzle-orm';
import { revalidatePath } from 'next/cache';
import { emitRealtimeEvent } from '@/lib/realtime';

export async function createIntervention(formData: FormData) {
  const { userId } = await auth();
  if (!userId) throw new Error('Unauthorized');

  const institutionId = getInstitutionId();
  const studentId = Number(formData.get('studentId'));
  const title = String(formData.get('title') || '').trim();
  const interventionType = String(formData.get('interventionType') || '').trim();

  if (!studentId || !title || !interventionType) {
    throw new Error('Student, title, and type are required');
  }

  const [created] = await db
    .insert(tables.interventions)
    .values({
      institutionId,
      studentId,
      title,
      interventionType,
      description: String(formData.get('description') || '').trim() || null,
      priority: String(formData.get('priority') || '').trim() || 'medium',
      status: String(formData.get('status') || '').trim() || 'planned',
      assignedTo: String(formData.get('assignedTo') || '').trim() || null,
      dueDate: formData.get('dueDate') ? new Date(String(formData.get('dueDate'))) : null
    })
    .returning();

  revalidatePath('/interventions');
  revalidatePath('/dashboard');
  emitRealtimeEvent({ type: 'data:mutation', paths: ['/interventions', '/dashboard'] });

  return created;
}

export async function updateInterventionStatus(interventionId: number, status: string) {
  const { userId } = await auth();
  if (!userId) throw new Error('Unauthorized');

  const institutionId = getInstitutionId();
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
        eq(tables.interventions.institutionId, institutionId)
      )
    )
    .returning();

  revalidatePath('/interventions');
  revalidatePath('/dashboard');
  emitRealtimeEvent({ type: 'data:mutation', paths: ['/interventions', '/dashboard'] });

  return updated;
}

export async function deleteIntervention(interventionId: number) {
  const { userId } = await auth();
  if (!userId) throw new Error('Unauthorized');

  const institutionId = getInstitutionId();
  const [deleted] = await db
    .delete(tables.interventions)
    .where(
      and(
        eq(tables.interventions.id, interventionId),
        eq(tables.interventions.institutionId, institutionId)
      )
    )
    .returning();

  revalidatePath('/interventions');
  revalidatePath('/dashboard');
  emitRealtimeEvent({ type: 'data:mutation', paths: ['/interventions', '/dashboard'] });

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
  const { userId } = await auth();
  if (!userId) throw new Error('Unauthorized');

  const institutionId = getInstitutionId();
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
        eq(tables.interventions.institutionId, institutionId)
      )
    )
    .returning();

  revalidatePath('/interventions');
  revalidatePath('/dashboard');
  emitRealtimeEvent({ type: 'data:mutation', paths: ['/interventions', '/dashboard'] });

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
