import InsightsPageClient from '@/components/insights-page';
import { loadStudentsWithRisk } from '@/lib/data/students';
import { loadLatestInsights } from '@/lib/data/insights';
import { requireTenantContext } from '@/lib/auth';

const toIso = (value: Date | string | null) => {
  if (!value) return null;
  if (value instanceof Date) return value.toISOString();
  return value;
};

export default async function InsightsPage() {
  const students = await loadStudentsWithRisk();
  const insights = await loadLatestInsights();
  const { institutionId } = await requireTenantContext();
  return (
    <InsightsPageClient
      initialStudents={students.map((student) => ({
        ...student,
        lastActivity: toIso(student.lastActivity),
        predictionDate: toIso(student.predictionDate)
      }))}
      initialInsights={insights.map((insight) => ({
        ...insight,
        createdAt: toIso(insight.createdAt)
      }))}
      initialInstitutionId={institutionId}
    />
  );
}
