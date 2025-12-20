import { loadStudentsWithRisk } from '@/lib/data/students';
import { loadLatestInsights } from '@/lib/data/insights';
import InsightsBoard from '@/components/insights-board';

export default async function InsightsPage({
  searchParams
}: {
  searchParams?: Promise<{ student?: string }>;
}) {
  const students = await loadStudentsWithRisk();
  const latestInsights = await loadLatestInsights(students.map((student) => student.id));
  const latestByStudent = new Map(
    latestInsights.map((insight) => [insight.studentDatabaseId, insight])
  );
  const resolvedParams = await searchParams;
  const highlightId = resolvedParams?.student ? Number(resolvedParams.student) : null;

  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-ink-400">GPT Insights</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink-50">Personalized recommendations</h1>
        <p className="mt-2 text-sm text-ink-300">
          Generate three concise recommendations based on the latest student context.
        </p>
      </div>
      <InsightsBoard
        students={students.map((student) => {
          const latest = latestByStudent.get(student.id);
          return {
            id: student.id,
            name: student.name,
            riskCategory: student.riskCategory,
            riskScore: student.riskScore,
            confidenceScore: student.confidenceScore,
            predictionDate:
              student.predictionDate instanceof Date
                ? student.predictionDate.toISOString()
                : student.predictionDate,
            cachedInsightHtml: latest?.formattedHtml ?? null,
            cachedInsightAt: latest?.createdAt ? latest.createdAt.toISOString() : null,
            cachedInsightRisk: latest?.riskLevel ?? null
          };
        })}
        highlightId={highlightId}
      />
      {students.length === 0 && (
        <div className="bg-panel rounded-3xl p-8 text-sm text-ink-300">
          Upload a gradebook to enable GPT insights.
        </div>
      )}
    </section>
  );
}
