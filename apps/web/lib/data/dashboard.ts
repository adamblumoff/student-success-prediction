import { auth } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { getInstitutionId } from '@/lib/auth';
import { eq, sql, and, gte, lt, desc } from 'drizzle-orm';

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

  const [{ latestPredictionDate }] = await db
    .select({ latestPredictionDate: sql<Date | null>`max(${tables.predictions.predictionDate})` })
    .from(tables.predictions)
    .where(eq(tables.predictions.institutionId, institutionId));

  const [{ recentPredictions }] = await db
    .select({ recentPredictions: sql<number>`count(*)` })
    .from(tables.predictions)
    .where(
      and(
        eq(tables.predictions.institutionId, institutionId),
        gte(tables.predictions.predictionDate, sql`now() - interval '7 days'`)
      )
    );

  const [{ previousPredictions }] = await db
    .select({ previousPredictions: sql<number>`count(*)` })
    .from(tables.predictions)
    .where(
      and(
        eq(tables.predictions.institutionId, institutionId),
        gte(tables.predictions.predictionDate, sql`now() - interval '14 days'`),
        lt(tables.predictions.predictionDate, sql`now() - interval '7 days'`)
      )
    );

  const [{ recentInterventions }] = await db
    .select({ recentInterventions: sql<number>`count(*)` })
    .from(tables.interventions)
    .where(
      and(
        eq(tables.interventions.institutionId, institutionId),
        gte(tables.interventions.createdAt, sql`now() - interval '7 days'`)
      )
    );

  const [{ completedInterventions }] = await db
    .select({ completedInterventions: sql<number>`count(*)` })
    .from(tables.interventions)
    .where(
      and(
        eq(tables.interventions.institutionId, institutionId),
        gte(tables.interventions.completedDate, sql`now() - interval '7 days'`)
      )
    );

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

  const topRisk = await db.execute<{
    studentId: number;
    studentIdentifier: string | null;
    name: string | null;
    gradeLevel: string | null;
    riskScore: number;
    riskCategory: string;
    confidenceScore: number | null;
  }>(sql`
    select
      s.id as "studentId",
      s.student_id as "studentIdentifier",
      s.name as "name",
      s.grade_level as "gradeLevel",
      p.risk_score as "riskScore",
      p.risk_category as "riskCategory",
      p.confidence_score as "confidenceScore"
    from ${tables.students} s
    join lateral (
      select risk_score, risk_category, confidence_score
      from ${tables.predictions} p
      where p.student_id = s.id
        and p.institution_id = ${institutionId}
      order by p.prediction_date desc
      limit 1
    ) p on true
    where s.institution_id = ${institutionId}
    order by p.risk_score desc
    limit 5
  `);

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
    topRiskStudents: topRisk.rows.map((row) => ({
      id: row.studentId,
      name: row.name,
      studentId: row.studentIdentifier,
      gradeLevel: row.gradeLevel,
      riskScore: row.riskScore,
      riskCategory: row.riskCategory,
      confidenceScore: row.confidenceScore
    }))
  };
}
