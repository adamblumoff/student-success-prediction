import InsightsPageClient from '@/components/insights-page';
import { loadStudentsWithRisk } from '@/lib/data/students';

const toIso = (value: Date | string | null) => {
  if (!value) return null;
  if (value instanceof Date) return value.toISOString();
  return value;
};

export default async function InsightsPage() {
  const students = await loadStudentsWithRisk();
  return (
    <InsightsPageClient
      initialStudents={students.map((student) => ({
        ...student,
        lastActivity: toIso(student.lastActivity),
        predictionDate: toIso(student.predictionDate)
      }))}
    />
  );
}
