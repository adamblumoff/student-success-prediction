'use server';

import { NextResponse } from 'next/server';
import { db, tables } from '@/db';
import { requireTenantContext } from '@/lib/auth';
import { sql } from 'drizzle-orm';

const toIso = (value: Date | string | null) => {
  if (!value) return null;
  if (value instanceof Date) return value.toISOString();
  return value;
};

export async function GET() {
  const { userId, districtId } = await requireTenantContext();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const studentsResult = await db.execute<{
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
      p.risk_category as "riskCategory",
      p.risk_score as "riskScore",
      p.confidence_score as "confidenceScore",
      p.prediction_date as "predictionDate"
    from ${tables.students} s
    left join lateral (
      select risk_category, risk_score, confidence_score, prediction_date
      from ${tables.predictions} p
      where p.student_id = s.id
        and p.district_id = ${districtId}
        and p.institution_id = s.institution_id
      order by p.prediction_date desc
      limit 1
    ) p on true
    left join lateral (
      select count(*)::int as active_count
      from ${tables.interventions} i
      where i.student_id = s.id
        and i.district_id = ${districtId}
        and i.institution_id = s.institution_id
        and (i.status is null or i.status != 'completed')
    ) i on true
    where s.district_id = ${districtId}
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
    order by g.student_database_id, g.created_at desc
  `);

  const interventionsResult = await db.execute<{
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
    order by i.created_at desc
  `);

  return NextResponse.json({
    students: studentsResult.rows.map((row) => ({
      ...row,
      lastActivity: toIso(row.lastActivity),
      predictionDate: toIso(row.predictionDate)
    })),
    insights: insightsResult.rows.map((row) => ({
      ...row,
      createdAt: toIso(row.createdAt)
    })),
    interventions: interventionsResult.rows.map((row) => ({
      ...row,
      dueDate: toIso(row.dueDate),
      createdAt: toIso(row.createdAt),
      completedDate: toIso(row.completedDate)
    }))
  });
}
