import InterventionsPageClient from '@/components/interventions-page';
import { listInterventions } from '@/lib/data/interventions';
import { loadStudentsWithRisk } from '@/lib/data/students';

const toIso = (value: Date | string | null) => {
  if (!value) return null;
  if (value instanceof Date) return value.toISOString();
  return value;
};

export default async function InterventionsPage() {
  const students = await loadStudentsWithRisk();
  const interventions = await listInterventions();

  const formattedStudents = students.map((student) => ({
    ...student,
    lastActivity: toIso(student.lastActivity),
    predictionDate: toIso(student.predictionDate)
  }));

  const formattedInterventions = interventions.map((row) => ({
    id: row.intervention.id,
    studentId: row.intervention.studentId,
    institutionId: row.intervention.institutionId,
    title: row.intervention.title ?? '',
    interventionType: row.intervention.interventionType ?? '',
    status: row.intervention.status,
    priority: row.intervention.priority,
    assignedTo: row.intervention.assignedTo,
    dueDate: toIso(row.intervention.dueDate),
    createdAt: toIso(row.intervention.createdAt),
    completedDate: toIso(row.intervention.completedDate),
    studentName: row.student?.name ?? null,
    studentIdentifier: row.student?.studentId ?? null
  }));

  return (
    <InterventionsPageClient
      initialStudents={formattedStudents}
      initialInterventions={formattedInterventions}
    />
  );
}
