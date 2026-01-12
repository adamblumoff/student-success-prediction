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
  const { userId, districtId } = await requireTenantContext();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const institutionParam = request.nextUrl.searchParams.get('institutionId');
  const institutionId = institutionParam ? Number(institutionParam) : null;
  const scopedInstitutionId =
    Number.isFinite(institutionId) && (institutionId ?? 0) > 0 ? institutionId : null;
  const includeInsightsParam = request.nextUrl.searchParams.get('includeInsights');
  const includeInsights = includeInsightsParam
    ? !['0', 'false', 'no'].includes(includeInsightsParam.toLowerCase())
    : true;
  const includeStudentsParam = request.nextUrl.searchParams.get('includeStudents');
  const includeStudents = includeStudentsParam
    ? !['0', 'false', 'no'].includes(includeStudentsParam.toLowerCase())
    : true;
  const includeInterventionsParam = request.nextUrl.searchParams.get('includeInterventions');
  const includeInterventions = includeInterventionsParam
    ? !['0', 'false', 'no'].includes(includeInterventionsParam.toLowerCase())
    : true;

  const studentsMeta = includeStudents
    ? await db.execute<{
        totalStudents: number;
        lastUpdated: Date | null;
      }>(sql`
        select
          count(*)::int as "totalStudents",
          max(
            greatest(
              coalesce(s.updated_at, s.created_at),
              coalesce(s.latest_prediction_date, s.created_at)
            )
          ) as "lastUpdated"
        from ${tables.students} s
        where s.district_id = ${districtId}
          ${scopedInstitutionId ? sql`and s.institution_id = ${scopedInstitutionId}` : sql``}
      `)
    : { rows: [] as Array<{ totalStudents: number; lastUpdated: Date | null }> };

  const studentsResult = includeStudents
    ? await db.execute<{
        id: number;
        institutionId: number;
        studentId: string;
        name: string | null;
        gradeLevel: string | null;
        currentGpa: number | null;
        attendanceRate: number | null;
        enrollmentStatus: string | null;
        assignedCounselor: string | null;
        lastActivity: Date | null;
        activeInterventions: number | null;
        riskCategory: string | null;
        riskScore: number | null;
        confidenceScore: number | null;
        predictionDate: Date | null;
      }>(sql`
      select
        s.id as "id",
        s.institution_id as "institutionId",
        s.student_id as "studentId",
        s.name as "name",
        s.grade_level as "gradeLevel",
        s.current_gpa as "currentGpa",
        s.attendance_rate as "attendanceRate",
        s.enrollment_status as "enrollmentStatus",
        s.assigned_counselor as "assignedCounselor",
        s.last_activity as "lastActivity",
        coalesce(i.active_count, 0) as "activeInterventions",
        s.latest_risk_category as "riskCategory",
        s.latest_risk_score as "riskScore",
        s.latest_confidence_score as "confidenceScore",
        s.latest_prediction_date as "predictionDate"
      from ${tables.students} s
      left join lateral (
        select count(*)::int as active_count
        from ${tables.interventions} i
        where i.student_id = s.id
          and i.district_id = ${districtId}
          and i.institution_id = s.institution_id
          and (i.status is null or i.status != 'completed')
      ) i on true
      where s.district_id = ${districtId}
        ${scopedInstitutionId ? sql`and s.institution_id = ${scopedInstitutionId}` : sql``}
    `)
    : { rows: [] as Array<{
        id: number;
        institutionId: number;
        studentId: string;
        name: string | null;
        gradeLevel: string | null;
        currentGpa: number | null;
        attendanceRate: number | null;
        enrollmentStatus: string | null;
        assignedCounselor: string | null;
        lastActivity: Date | null;
        activeInterventions: number | null;
        riskCategory: string | null;
        riskScore: number | null;
        confidenceScore: number | null;
        predictionDate: Date | null;
      }> };

  const insightsMeta = includeInsights
    ? await db.execute<{
        totalInsights: number;
        lastUpdated: Date | null;
      }>(sql`
        select
          count(*)::int as "totalInsights",
          max(coalesce(g.updated_at, g.created_at)) as "lastUpdated"
        from ${tables.gptInsights} g
        where g.district_id = ${districtId}
          ${scopedInstitutionId ? sql`and g.institution_id = ${scopedInstitutionId}` : sql``}
      `)
    : { rows: [] as Array<{ totalInsights: number; lastUpdated: Date | null }> };

  const insightsResult = includeInsights
    ? await db.execute<{
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
          ${scopedInstitutionId ? sql`and g.institution_id = ${scopedInstitutionId}` : sql``}
        order by g.student_database_id, g.created_at desc
      `)
    : { rows: [] as Array<{
        studentDatabaseId: number;
        institutionId: number;
        formattedHtml: string | null;
        riskLevel: string | null;
        createdAt: Date | null;
      }> };

  const interventionsMeta = includeInterventions
    ? await db.execute<{
        totalInterventions: number;
        lastUpdated: Date | null;
      }>(sql`
        select
          count(*)::int as "totalInterventions",
          max(
            greatest(
              coalesce(i.updated_at, i.created_at),
              coalesce(i.completed_date, i.created_at)
            )
          ) as "lastUpdated"
        from ${tables.interventions} i
        where i.district_id = ${districtId}
          ${scopedInstitutionId ? sql`and i.institution_id = ${scopedInstitutionId}` : sql``}
      `)
    : { rows: [] as Array<{ totalInterventions: number; lastUpdated: Date | null }> };

  const interventionsResult = includeInterventions
    ? await db.execute<{
    id: number;
    studentId: number | null;
    institutionId: number;
    title: string;
    interventionType: string;
    status: string | null;
    priority: string | null;
    assignedTo: string | null;
    dueDate: Date | null;
    createdAt: Date | null;
    completedDate: Date | null;
    studentName: string | null;
    studentIdentifier: string | null;
    }>(sql`
      select
        i.id as "id",
        i.student_id as "studentId",
        i.institution_id as "institutionId",
        i.title as "title",
        i.intervention_type as "interventionType",
        i.status as "status",
        i.priority as "priority",
        i.assigned_to as "assignedTo",
        i.due_date as "dueDate",
        i.created_at as "createdAt",
        i.completed_date as "completedDate",
        s.name as "studentName",
        s.student_id as "studentIdentifier"
      from ${tables.interventions} i
      left join ${tables.students} s
        on i.student_id = s.id
      where i.district_id = ${districtId}
        ${scopedInstitutionId ? sql`and i.institution_id = ${scopedInstitutionId}` : sql``}
      order by i.created_at desc
    `)
    : { rows: [] as Array<{
        id: number;
        studentId: number | null;
        institutionId: number;
        title: string;
        interventionType: string;
        status: string | null;
        priority: string | null;
        assignedTo: string | null;
        dueDate: Date | null;
        createdAt: Date | null;
        completedDate: Date | null;
        studentName: string | null;
        studentIdentifier: string | null;
      }> };

  const studentsMetaRow = studentsMeta.rows[0];
  const insightsMetaRow = insightsMeta.rows[0];
  const interventionsMetaRow = interventionsMeta.rows[0];
  const studentsVersion = includeStudents
    ? [
        `count:${studentsMetaRow?.totalStudents ?? 0}`,
        `updated:${toIso(studentsMetaRow?.lastUpdated ?? null) ?? '0'}`
      ].join('|')
    : null;
  const insightsVersion = includeInsights
    ? [
        `count:${insightsMetaRow?.totalInsights ?? 0}`,
        `updated:${toIso(insightsMetaRow?.lastUpdated ?? null) ?? '0'}`
      ].join('|')
    : null;
  const interventionsVersion = includeInterventions
    ? [
        `count:${interventionsMetaRow?.totalInterventions ?? 0}`,
        `updated:${toIso(interventionsMetaRow?.lastUpdated ?? null) ?? '0'}`
      ].join('|')
    : null;

  return NextResponse.json({
    students: studentsResult.rows.map((row) => ({
      ...row,
      lastActivity: toIso(row.lastActivity),
      predictionDate: toIso(row.predictionDate)
    })),
    studentsVersion,
    insights: insightsResult.rows.map((row) => ({
      ...row,
      createdAt: toIso(row.createdAt)
    })),
    insightsVersion,
    interventions: interventionsResult.rows.map((row) => ({
      ...row,
      dueDate: toIso(row.dueDate),
      createdAt: toIso(row.createdAt),
      completedDate: toIso(row.completedDate)
    })),
    interventionsVersion
  });
}
