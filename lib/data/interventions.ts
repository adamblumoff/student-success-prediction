import { auth } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { getInstitutionId } from '@/lib/auth';
import { eq, desc } from 'drizzle-orm';

export async function listInterventions() {
  const { userId } = await auth();
  if (!userId) throw new Error('Unauthorized');

  const institutionId = getInstitutionId();
  const rows = await db
    .select({
      intervention: tables.interventions,
      student: tables.students
    })
    .from(tables.interventions)
    .leftJoin(tables.students, eq(tables.interventions.studentId, tables.students.id))
    .where(eq(tables.interventions.institutionId, institutionId))
    .orderBy(desc(tables.interventions.createdAt));

  return rows;
}
