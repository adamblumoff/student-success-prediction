'use server';

import { db, tables } from '@/db';
import { requireTenantContext } from '@/lib/auth';
import { and, eq, inArray } from 'drizzle-orm';
import { revalidatePath, revalidateTag } from 'next/cache';
import { emitRealtimeEvent } from '@/lib/realtime';
import { assignCounselorSchema, deleteStudentsSchema } from '@/lib/validation';

export async function deleteStudentsAction(studentIds: number[]) {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) {
    throw new Error('Unauthorized');
  }

  const parsed = deleteStudentsSchema.parse({ studentIds });
  if (parsed.studentIds.length === 0) {
    return { deletedIds: [] as number[], deletedCount: 0 };
  }

  const rows = await db
    .select({ id: tables.students.id })
    .from(tables.students)
    .where(
      and(
        eq(tables.students.districtId, districtId),
        eq(tables.students.institutionId, institutionId),
        inArray(tables.students.id, parsed.studentIds)
      )
    );

  const authorizedIds = rows.map((row) => row.id);
  if (authorizedIds.length === 0) {
    return { deletedIds: [] as number[], deletedCount: 0 };
  }

  await db.transaction(async (tx) => {
    await tx
      .delete(tables.gptInsights)
      .where(
        and(
          eq(tables.gptInsights.districtId, districtId),
          eq(tables.gptInsights.institutionId, institutionId),
          inArray(tables.gptInsights.studentDatabaseId, authorizedIds)
        )
      );

    await tx
      .delete(tables.predictions)
      .where(
        and(
          eq(tables.predictions.districtId, districtId),
          eq(tables.predictions.institutionId, institutionId),
          inArray(tables.predictions.studentId, authorizedIds)
        )
      );

    await tx
      .delete(tables.interventions)
      .where(
        and(
          eq(tables.interventions.districtId, districtId),
          eq(tables.interventions.institutionId, institutionId),
          inArray(tables.interventions.studentId, authorizedIds)
        )
      );

    await tx
      .delete(tables.students)
      .where(
        and(
          eq(tables.students.districtId, districtId),
          eq(tables.students.institutionId, institutionId),
          inArray(tables.students.id, authorizedIds)
        )
      );
  });

  revalidatePath('/students');
  revalidatePath('/dashboard');
  revalidatePath('/insights');
  revalidateTag('dashboard-stats', { expire: 0 });
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/students', '/dashboard', '/insights']
  });

  return { deletedIds: authorizedIds, deletedCount: authorizedIds.length };
}

export async function assignCounselorAction(studentIds: number[], counselor: string) {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) {
    throw new Error('Unauthorized');
  }

  const parsed = assignCounselorSchema.parse({ studentIds, counselor });
  if (parsed.studentIds.length === 0) {
    return { updatedIds: [] as number[], updatedCount: 0 };
  }

  const trimmedCounselor = parsed.counselor.trim();

  const rows = await db
    .select({ id: tables.students.id })
    .from(tables.students)
    .where(
      and(
        eq(tables.students.districtId, districtId),
        eq(tables.students.institutionId, institutionId),
        inArray(tables.students.id, parsed.studentIds)
      )
    );

  const authorizedIds = rows.map((row) => row.id);
  if (authorizedIds.length === 0) {
    return { updatedIds: [] as number[], updatedCount: 0 };
  }

  await db
    .update(tables.students)
    .set({ assignedCounselor: trimmedCounselor, updatedAt: new Date() })
    .where(
      and(
        eq(tables.students.districtId, districtId),
        eq(tables.students.institutionId, institutionId),
        inArray(tables.students.id, authorizedIds)
      )
    );

  revalidatePath('/students');
  revalidateTag('dashboard-stats', { expire: 0 });
  emitRealtimeEvent({ type: 'data:mutation', paths: ['/students'] });

  return { updatedIds: authorizedIds, updatedCount: authorizedIds.length };
}
