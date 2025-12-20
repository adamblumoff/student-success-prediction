import { auth } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { getInstitutionId } from '@/lib/auth';
import { eq, and, sql } from 'drizzle-orm';

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

export async function loadStudentsWithRisk() {
  const { userId } = await auth();
  if (!userId) {
    throw new Error('Unauthorized');
  }

  const institutionId = getInstitutionId();
  const results = await db.execute<{
    id: number;
    studentId: string;
    name: string | null;
    gradeLevel: string | null;
    currentGpa: number | null;
    attendanceRate: number | null;
    enrollmentStatus: string | null;
    lastActivity: Date | null;
    activeInterventions: number | null;
    riskCategory: string | null;
    riskScore: number | null;
    confidenceScore: number | null;
    predictionDate: Date | null;
  }>(sql`
    select
      s.id as "id",
      s.student_id as "studentId",
      s.name as "name",
      s.grade_level as "gradeLevel",
      s.current_gpa as "currentGpa",
      s.attendance_rate as "attendanceRate",
      s.enrollment_status as "enrollmentStatus",
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
      where p.student_id = s.id and p.institution_id = ${institutionId}
      order by p.prediction_date desc
      limit 1
    ) p on true
    left join lateral (
      select count(*)::int as active_count
      from ${tables.interventions} i
      where i.student_id = s.id
        and i.institution_id = ${institutionId}
        and (i.status is null or i.status != 'completed')
    ) i on true
    where s.institution_id = ${institutionId}
    limit 500
  `);

  return results.rows;
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
