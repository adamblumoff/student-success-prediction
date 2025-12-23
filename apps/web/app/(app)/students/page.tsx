import StudentsPageClient from '@/components/students-page';
import { loadStudentsWithRisk } from '@/lib/data/students';
import { requireTenantContext } from '@/lib/auth';

const toIso = (value: Date | string | null) => {
  if (!value) return null;
  if (value instanceof Date) return value.toISOString();
  return value;
};

export default async function StudentsPage() {
  const students = await loadStudentsWithRisk();
  const { institutionId } = await requireTenantContext();
  return (
    <StudentsPageClient
      initialStudents={students.map((student) => ({
        ...student,
        lastActivity: toIso(student.lastActivity),
        predictionDate: toIso(student.predictionDate)
      }))}
      initialInstitutionId={institutionId}
    />
  );
}
