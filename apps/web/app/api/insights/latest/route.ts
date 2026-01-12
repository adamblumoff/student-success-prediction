'use server';

import { NextResponse, type NextRequest } from 'next/server';
import { db, tables } from '@/db';
import { requireTenantContext } from '@/lib/auth';
import { sql } from 'drizzle-orm';

const toIso = (value: Date | string | null) => {
  if (!value) return null;
  if (value instanceof Date) return value.toISOString();
  return value;
};

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

  const insightsMeta = await db.execute<{
    totalInsights: number;
    lastUpdated: Date | null;
  }>(sql`
    select
      count(*)::int as "totalInsights",
      max(coalesce(g.updated_at, g.created_at)) as "lastUpdated"
    from ${tables.gptInsights} g
    where g.district_id = ${districtId}
      and g.institution_id = ${resolvedInstitutionId}
  `);

  const insightsResult = await db.execute<{
    studentDatabaseId: number;
    institutionId: number;
    formattedHtml: string | null;
    riskLevel: string | null;
    createdAt: Date | null;
  }>(sql`
    select distinct on (g.student_database_id)
      g.student_database_id as "studentDatabaseId",
      g.institution_id as "institutionId",
      g.formatted_html as "formattedHtml",
      g.risk_level as "riskLevel",
      g.created_at as "createdAt"
    from ${tables.gptInsights} g
    where g.district_id = ${districtId}
      and g.institution_id = ${resolvedInstitutionId}
    order by g.student_database_id, g.created_at desc
  `);

  const metaRow = insightsMeta.rows[0];
  const version = [
    `count:${metaRow?.totalInsights ?? 0}`,
    `updated:${toIso(metaRow?.lastUpdated ?? null) ?? '0'}`
  ].join('|');

  return NextResponse.json({
    insights: insightsResult.rows.map((row) => ({
      ...row,
      createdAt: toIso(row.createdAt)
    })),
    version
  });
}
