import { db, tables } from '@/db';
import { requireTenantContext } from '@/lib/auth';
import { eq, and, sql } from 'drizzle-orm';

export async function loadExistingStudents() {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) {
    throw new Error('Unauthorized');
  }
  const results = await db
    .select()
    .from(tables.students)
    .where(
      and(
        eq(tables.students.districtId, districtId),
        eq(tables.students.institutionId, institutionId)
      )
    );

  return results;
}

export async function loadStudentsWithRisk() {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) {
    throw new Error('Unauthorized');
  }
  const results = await db.execute<{
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
      where p.student_id = s.id and p.district_id = ${districtId}
        and p.institution_id = ${institutionId}
      order by p.prediction_date desc
      limit 1
    ) p on true
    left join lateral (
      select count(*)::int as active_count
      from ${tables.interventions} i
      where i.student_id = s.id
        and i.district_id = ${districtId}
        and i.institution_id = ${institutionId}
        and (i.status is null or i.status != 'completed')
    ) i on true
    where s.district_id = ${districtId}
      and s.institution_id = ${institutionId}
  `);

  return results.rows;
}

export async function getStudentPredictions(studentDbId: number) {
  const { userId, districtId, institutionId } = await requireTenantContext();
  if (!userId) {
    throw new Error('Unauthorized');
  }
  const results = await db
    .select()
    .from(tables.predictions)
    .where(
      and(
        eq(tables.predictions.districtId, districtId),
        eq(tables.predictions.institutionId, institutionId),
        eq(tables.predictions.studentId, studentDbId)
      )
    )
    .orderBy(tables.predictions.predictionDate);

  return results;
}
