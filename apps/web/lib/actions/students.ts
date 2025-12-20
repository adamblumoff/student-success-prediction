'use server';

import { auth } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { getInstitutionId } from '@/lib/auth';
import { and, eq, inArray } from 'drizzle-orm';
import { revalidatePath } from 'next/cache';
import { emitRealtimeEvent } from '@/lib/realtime';

export async function deleteStudentsAction(studentIds: number[]) {
  const { userId } = await auth();
  if (!userId) {
    throw new Error('Unauthorized');
  }

  if (!Array.isArray(studentIds) || studentIds.length === 0) {
    return { deletedIds: [] as number[], deletedCount: 0 };
  }

  const institutionId = getInstitutionId();

  const rows = await db
    .select({ id: tables.students.id })
    .from(tables.students)
    .where(
      and(
        eq(tables.students.institutionId, institutionId),
        inArray(tables.students.id, studentIds)
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
          eq(tables.gptInsights.institutionId, institutionId),
          inArray(tables.gptInsights.studentDatabaseId, authorizedIds)
        )
      );

    await tx
      .delete(tables.predictions)
      .where(inArray(tables.predictions.studentId, authorizedIds));

    await tx
      .delete(tables.interventions)
      .where(inArray(tables.interventions.studentId, authorizedIds));

    await tx
      .delete(tables.students)
      .where(inArray(tables.students.id, authorizedIds));
  });

  revalidatePath('/students');
  revalidatePath('/dashboard');
  revalidatePath('/insights');
  emitRealtimeEvent({
    type: 'data:mutation',
    paths: ['/students', '/dashboard', '/insights']
  });

  return { deletedIds: authorizedIds, deletedCount: authorizedIds.length };
}
