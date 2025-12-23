import { db, tables } from '@/db';
import { requireTenantContext } from '@/lib/auth';
import { eq, sql, and, gte, lt, desc, isNotNull } from 'drizzle-orm';

export async function getDashboardStats() {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) throw new Error('Unauthorized');

  const [{ totalStudents }] = await db
    .select({ totalStudents: sql<number>`count(*)` })
    .from(tables.students)
    .where(
      and(
        eq(tables.students.districtId, districtId),
        eq(tables.students.institutionId, institutionId)
      )
    );

  const [{ totalPredictions }] = await db
    .select({
      totalPredictions: sql<number>`count(*) filter (where ${tables.students.latestPredictionDate} is not null)`
    })
    .from(tables.students)
    .where(
      and(
        eq(tables.students.districtId, districtId),
        eq(tables.students.institutionId, institutionId)
      )
    );

  const [{ totalInterventions }] = await db
    .select({ totalInterventions: sql<number>`count(*)` })
    .from(tables.interventions)
    .where(
      and(
        eq(tables.interventions.districtId, districtId),
        eq(tables.interventions.institutionId, institutionId)
      )
    );

  const [{ latestPredictionDate }] = await db
    .select({
      latestPredictionDate: sql<Date | null>`max(${tables.students.latestPredictionDate})`
    })
    .from(tables.students)
    .where(
      and(
        eq(tables.students.districtId, districtId),
        eq(tables.students.institutionId, institutionId)
      )
    );

  const [{ recentPredictions }] = await db
    .select({ recentPredictions: sql<number>`count(*)` })
    .from(tables.students)
    .where(
      and(
        eq(tables.students.districtId, districtId),
        eq(tables.students.institutionId, institutionId),
        gte(tables.students.latestPredictionDate, sql`now() - interval '7 days'`)
      )
    );

  const [{ previousPredictions }] = await db
    .select({ previousPredictions: sql<number>`count(*)` })
    .from(tables.students)
    .where(
      and(
        eq(tables.students.districtId, districtId),
        eq(tables.students.institutionId, institutionId),
        gte(tables.students.latestPredictionDate, sql`now() - interval '14 days'`),
        lt(tables.students.latestPredictionDate, sql`now() - interval '7 days'`)
      )
    );

  const [{ recentInterventions }] = await db
    .select({ recentInterventions: sql<number>`count(*)` })
    .from(tables.interventions)
    .where(
      and(
        eq(tables.interventions.districtId, districtId),
        eq(tables.interventions.institutionId, institutionId),
        gte(tables.interventions.createdAt, sql`now() - interval '7 days'`)
      )
    );

  const [{ completedInterventions }] = await db
    .select({ completedInterventions: sql<number>`count(*)` })
    .from(tables.interventions)
    .where(
      and(
        eq(tables.interventions.districtId, districtId),
        eq(tables.interventions.institutionId, institutionId),
        gte(tables.interventions.completedDate, sql`now() - interval '7 days'`)
      )
    );

  const riskBuckets = await db
    .select({
      riskCategory: tables.students.latestRiskCategory,
      count: sql<number>`count(*)`
    })
    .from(tables.students)
    .where(
      and(
        eq(tables.students.districtId, districtId),
        eq(tables.students.institutionId, institutionId),
        isNotNull(tables.students.latestRiskScore)
      )
    )
    .groupBy(tables.students.latestRiskCategory);

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

  const topRisk = await db
    .select({
      studentId: tables.students.id,
      studentIdentifier: tables.students.studentId,
      name: tables.students.name,
      gradeLevel: tables.students.gradeLevel,
      riskScore: tables.students.latestRiskScore,
      riskCategory: tables.students.latestRiskCategory,
      confidenceScore: tables.students.latestConfidenceScore
    })
    .from(tables.students)
    .where(
      and(
        eq(tables.students.districtId, districtId),
        eq(tables.students.institutionId, institutionId)
      )
    )
    .orderBy(desc(tables.students.latestRiskScore))
    .limit(5);

  return {
    totalStudents: Number(totalStudents ?? 0),
    totalPredictions: Number(totalPredictions ?? 0),
    totalInterventions: Number(totalInterventions ?? 0),
    riskDistribution: distribution,
    latestPredictionDate,
    recentPredictions: Number(recentPredictions ?? 0),
    previousPredictions: Number(previousPredictions ?? 0),
    recentInterventions: Number(recentInterventions ?? 0),
    completedInterventions: Number(completedInterventions ?? 0),
    topRiskStudents: topRisk.map((row) => ({
      id: row.studentId,
      name: row.name,
      studentId: row.studentIdentifier,
      gradeLevel: row.gradeLevel,
      riskScore: row.riskScore ?? 0,
      riskCategory: row.riskCategory ?? null,
      confidenceScore: row.confidenceScore ?? null
    }))
  };
}
