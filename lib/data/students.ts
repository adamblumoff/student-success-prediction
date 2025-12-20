import { auth } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { getInstitutionId } from '@/lib/auth';
import { eq, and } from 'drizzle-orm';

export async function loadExistingStudents() {
  const { userId } = await auth();
  if (!userId) {
    throw new Error('Unauthorized');
  }

  const institutionId = getInstitutionId();
  const results = await db
    .select()
    .from(tables.students)
    .where(eq(tables.students.institutionId, institutionId))
    .limit(500);

  return results;
}

export async function getStudentPredictions(studentDbId: number) {
  const { userId } = await auth();
  if (!userId) {
    throw new Error('Unauthorized');
  }

  const institutionId = getInstitutionId();
  const results = await db
    .select()
    .from(tables.predictions)
    .where(
      and(
        eq(tables.predictions.institutionId, institutionId),
        eq(tables.predictions.studentId, studentDbId)
      )
    )
    .orderBy(tables.predictions.predictionDate);

  return results;
}
