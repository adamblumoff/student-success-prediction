'use client';

import { useEffect, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import InsightsBoard from '@/components/insights-board';
import { useAppData, type StudentWithRisk } from '@/components/app-data-provider';

export default function InsightsPageClient({
  initialStudents
}: {
  initialStudents: StudentWithRisk[];
}) {
  const {
    students: contextStudents,
    selectedInstitutionId,
    seedStudentsForInstitution,
    loadInsightsForInstitution,
    isLoadingInsights,
    insights
  } = useAppData();
  const searchParams = useSearchParams();
  const highlightId = searchParams.get('student');
  const highlightStudentId = highlightId ? Number(highlightId) : null;

  useEffect(() => {
    if (!selectedInstitutionId) return;
    if (initialStudents.length === 0) return;
    seedStudentsForInstitution(selectedInstitutionId, initialStudents);
  }, [initialStudents, seedStudentsForInstitution, selectedInstitutionId]);

  useEffect(() => {
    if (!selectedInstitutionId) return;
    void loadInsightsForInstitution(selectedInstitutionId);
  }, [loadInsightsForInstitution, selectedInstitutionId]);

  const students = useMemo(
    () => (contextStudents.length > 0 ? contextStudents : initialStudents),
    [contextStudents, initialStudents]
  );

  const latestByStudent = useMemo(() => {
    const map = new Map<number, (typeof insights)[number]>();
    for (const insight of insights) {
      if (!map.has(insight.studentDatabaseId)) {
        map.set(insight.studentDatabaseId, insight);
      }
    }
    return map;
  }, [insights]);

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
            predictionDate: student.predictionDate,
            cachedInsightHtml: latest?.formattedHtml ?? null,
            cachedInsightAt: latest?.createdAt ?? null,
            cachedInsightRisk: latest?.riskLevel ?? null
          };
        })}
        highlightId={Number.isFinite(highlightStudentId ?? NaN) ? highlightStudentId : null}
      />
      {isLoadingInsights && (
        <p className="text-xs uppercase tracking-[0.35em] text-ink-400">
          Loading cached insights…
        </p>
      )}
      {students.length === 0 && (
        <div className="bg-panel rounded-3xl p-8 text-sm text-ink-300">
          Upload a gradebook to enable GPT insights.
        </div>
      )}
    </section>
  );
}
