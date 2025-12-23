'use server';

import { NextResponse, type NextRequest } from 'next/server';
import { db, tables } from '@/db';
import { requireTenantContext } from '@/lib/auth';
import { sql } from 'drizzle-orm';
import { unstable_cache } from 'next/cache';

const toIso = (value: Date | string | null) => {
  if (!value) return null;
  if (value instanceof Date) return value.toISOString();
  return value;
};

const loadDashboardStats = (districtId: number, resolvedInstitutionId: number) =>
  unstable_cache(
    async () => {
    const studentStats = await db.execute<{
      totalStudents: number;
      totalPredictions: number;
      latestPredictionDate: Date | null;
      recentPredictions: number;
      previousPredictions: number;
      highRisk: number;
      mediumRisk: number;
      lowRisk: number;
      unknownRisk: number;
    }>(sql`
      select
        count(*)::int as "totalStudents",
        count(*) filter (where s.latest_prediction_date is not null)::int as "totalPredictions",
        max(s.latest_prediction_date) as "latestPredictionDate",
        count(*) filter (where s.latest_prediction_date >= now() - interval '7 days')::int as "recentPredictions",
        count(*) filter (
          where s.latest_prediction_date < now() - interval '7 days'
            and s.latest_prediction_date >= now() - interval '14 days'
        )::int as "previousPredictions",
        count(*) filter (where s.latest_risk_category ilike 'high%')::int as "highRisk",
        count(*) filter (
          where s.latest_risk_category ilike 'moderate%' or s.latest_risk_category ilike 'medium%'
        )::int as "mediumRisk",
        count(*) filter (where s.latest_risk_category ilike 'low%')::int as "lowRisk",
        count(*) filter (where s.latest_risk_category is null)::int as "unknownRisk"
      from ${tables.students} s
      where s.district_id = ${districtId}
        and s.institution_id = ${resolvedInstitutionId}
    `);

    const topRiskStudents = await db.execute<{
      id: number;
      name: string | null;
      studentId: string;
      gradeLevel: string | null;
      riskScore: number | null;
      riskCategory: string | null;
      confidenceScore: number | null;
    }>(sql`
      select
        s.id as "id",
        s.name as "name",
        s.student_id as "studentId",
        s.grade_level as "gradeLevel",
        s.latest_risk_score as "riskScore",
        s.latest_risk_category as "riskCategory",
        s.latest_confidence_score as "confidenceScore"
      from ${tables.students} s
      where s.district_id = ${districtId}
        and s.institution_id = ${resolvedInstitutionId}
        and s.latest_risk_score is not null
      order by s.latest_risk_score desc
      limit 5
    `);

    const interventionsStats = await db.execute<{
      totalInterventions: number;
      recentInterventions: number;
      completedInterventions: number;
    }>(sql`
      select
        count(*)::int as "totalInterventions",
        count(*) filter (where created_at >= now() - interval '7 days')::int as "recentInterventions",
        count(*) filter (where completed_date >= now() - interval '7 days')::int as "completedInterventions"
      from ${tables.interventions}
      where district_id = ${districtId}
        and institution_id = ${resolvedInstitutionId}
    `);

    const studentsRow = studentStats.rows[0];
    const interventionsRow = interventionsStats.rows[0];

    return {
      totalStudents: studentsRow?.totalStudents ?? 0,
      totalPredictions: studentsRow?.totalPredictions ?? 0,
      totalInterventions: interventionsRow?.totalInterventions ?? 0,
      riskDistribution: {
        high: studentsRow?.highRisk ?? 0,
        medium: studentsRow?.mediumRisk ?? 0,
        low: studentsRow?.lowRisk ?? 0,
        unknown: studentsRow?.unknownRisk ?? 0
      },
      latestPredictionDate: toIso(studentsRow?.latestPredictionDate ?? null),
      recentPredictions: studentsRow?.recentPredictions ?? 0,
      previousPredictions: studentsRow?.previousPredictions ?? 0,
      recentInterventions: interventionsRow?.recentInterventions ?? 0,
      completedInterventions: interventionsRow?.completedInterventions ?? 0,
      topRiskStudents: topRiskStudents.rows
    };
    },
    ['dashboard-stats', String(districtId), String(resolvedInstitutionId)],
    {
      revalidate: 60,
      tags: ['dashboard-stats']
    }
  )();

export async function GET(request: NextRequest) {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const institutionParam = request.nextUrl.searchParams.get('institutionId');
  const requestedInstitutionId = institutionParam ? Number(institutionParam) : null;
  const resolvedInstitutionId =
    Number.isFinite(requestedInstitutionId) && (requestedInstitutionId ?? 0) > 0
      ? requestedInstitutionId
      : institutionId;

  if (!resolvedInstitutionId) {
    return NextResponse.json({ error: 'Missing institutionId' }, { status: 400 });
  }

  const stats = await loadDashboardStats(districtId, resolvedInstitutionId);
  return NextResponse.json(stats);
}
