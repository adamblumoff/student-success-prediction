import { db, tables } from '@/db';
import { requireTenantContext } from '@/lib/auth';
import { sql } from 'drizzle-orm';

export async function loadLatestInsights() {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) {
    throw new Error('Unauthorized');
  }

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
      and g.institution_id = ${institutionId}
    order by g.student_database_id, g.created_at desc
  `);

  return insightsResult.rows;
}
