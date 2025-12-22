import { db, tables } from '@/db';
import { requireTenantContext } from '@/lib/auth';
import { and, eq, desc } from 'drizzle-orm';

export async function listInterventions() {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) throw new Error('Unauthorized');
  const rows = await db
    .select({
      intervention: tables.interventions,
      student: tables.students
    })
    .from(tables.interventions)
    .leftJoin(tables.students, eq(tables.interventions.studentId, tables.students.id))
    .where(
      and(
        eq(tables.interventions.districtId, districtId),
        eq(tables.interventions.institutionId, institutionId)
      )
    )
    .orderBy(desc(tables.interventions.createdAt));

  return rows;
}
