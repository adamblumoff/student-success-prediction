import { loadExistingStudents } from '@/lib/data/students';
import InsightCard from '@/components/insight-card';

export default async function InsightsPage({
  searchParams
}: {
  searchParams?: Promise<{ student?: string }>;
}) {
  const students = await loadExistingStudents();
  const resolvedParams = await searchParams;
  const highlightId = resolvedParams?.student ? Number(resolvedParams.student) : null;

  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-ink-400">GPT Insights</p>
        <h1 className="mt-2 text-3xl font-semibold">Personalized recommendations</h1>
        <p className="mt-2 text-sm text-ink-600">
          Generate three concise recommendations based on the latest student context.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {students.map((student) => (
          <InsightCard
            key={student.id}
            studentId={student.id}
            name={student.name}
            highlight={highlightId === student.id}
          />
        ))}
      </div>
      {students.length === 0 && (
        <div className="bg-panel rounded-3xl p-8 text-sm text-ink-600">
          Upload a gradebook to enable GPT insights.
        </div>
      )}
    </section>
  );
}
