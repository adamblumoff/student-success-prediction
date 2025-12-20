import { auth } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { getInstitutionId } from '@/lib/auth';
import { eq, sql } from 'drizzle-orm';

export async function getDashboardStats() {
  const { userId } = await auth();
  if (!userId) throw new Error('Unauthorized');

  const institutionId = getInstitutionId();

  const [{ totalStudents }] = await db
    .select({ totalStudents: sql<number>`count(*)` })
    .from(tables.students)
    .where(eq(tables.students.institutionId, institutionId));

  const [{ totalPredictions }] = await db
    .select({ totalPredictions: sql<number>`count(*)` })
    .from(tables.predictions)
    .where(eq(tables.predictions.institutionId, institutionId));

  const [{ totalInterventions }] = await db
    .select({ totalInterventions: sql<number>`count(*)` })
    .from(tables.interventions)
    .where(eq(tables.interventions.institutionId, institutionId));

  const riskBuckets = await db
    .select({
      riskCategory: tables.predictions.riskCategory,
      count: sql<number>`count(*)`
    })
    .from(tables.predictions)
    .where(eq(tables.predictions.institutionId, institutionId))
    .groupBy(tables.predictions.riskCategory);

  const distribution = riskBuckets.reduce(
    (acc, bucket) => {
      const key = (bucket.riskCategory || 'Unknown').toLowerCase();
      if (key.includes('high')) acc.high += Number(bucket.count);
      else if (key.includes('moderate') || key.includes('medium')) acc.medium += Number(bucket.count);
      else if (key.includes('low')) acc.low += Number(bucket.count);
      else acc.unknown += Number(bucket.count);
      return acc;
    },
    { high: 0, medium: 0, low: 0, unknown: 0 }
  );

  return {
    totalStudents: Number(totalStudents ?? 0),
    totalPredictions: Number(totalPredictions ?? 0),
    totalInterventions: Number(totalInterventions ?? 0),
    riskDistribution: distribution
  };
}
