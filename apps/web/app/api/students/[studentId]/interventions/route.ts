import { auth } from '@clerk/nextjs/server';
import { db, tables } from '@/db';
import { getInstitutionId } from '@/lib/auth';
import { and, desc, eq } from 'drizzle-orm';

export const dynamic = 'force-dynamic';

export async function GET(
  _request: Request,
  { params }: { params: { studentId: string } }
) {
  const { userId } = await auth();
  if (!userId) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  const studentId = Number(params.studentId);
  if (!Number.isFinite(studentId)) {
    return new Response(JSON.stringify({ error: 'Invalid student id' }), { status: 400 });
  }

  const institutionId = getInstitutionId();
  const [student] = await db
    .select({
      id: tables.students.id,
      name: tables.students.name,
      studentId: tables.students.studentId,
      gradeLevel: tables.students.gradeLevel,
      enrollmentStatus: tables.students.enrollmentStatus
    })
    .from(tables.students)
    .where(and(eq(tables.students.id, studentId), eq(tables.students.institutionId, institutionId)))
    .limit(1);

  if (!student) {
    return new Response(JSON.stringify({ error: 'Student not found' }), { status: 404 });
  }

  const interventions = await db
    .select({
      id: tables.interventions.id,
      title: tables.interventions.title,
      interventionType: tables.interventions.interventionType,
      description: tables.interventions.description,
      status: tables.interventions.status,
      priority: tables.interventions.priority,
      assignedTo: tables.interventions.assignedTo,
      dueDate: tables.interventions.dueDate,
      createdAt: tables.interventions.createdAt
    })
    .from(tables.interventions)
    .where(
      and(
        eq(tables.interventions.institutionId, institutionId),
        eq(tables.interventions.studentId, studentId)
      )
    )
    .orderBy(desc(tables.interventions.createdAt));

  return Response.json({ student, interventions });
}
