'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import InsightsBoard from '@/components/insights-board';
import { useAppData, type StudentWithRisk } from '@/components/app-data-provider';

export default function InsightsPageClient({
  initialStudents,
  initialInsights,
  initialInstitutionId
}: {
  initialStudents: StudentWithRisk[];
  initialInsights: {
    studentDatabaseId: number;
    institutionId: number;
    formattedHtml: string | null;
    riskLevel: string | null;
    createdAt: string | null;
  }[];
  initialInstitutionId: number | null;
}) {
  const {
    students: contextStudents,
    selectedInstitutionId,
    seedStudentsForInstitution,
    seedInsightsForInstitution,
    loadInsightsForInstitution,
    isLoadingInsights,
    insights
  } = useAppData();
  const [hasPending, setHasPending] = useState(false);
  const searchParams = useSearchParams();
  const highlightId = searchParams.get('student');
  const highlightStudentId = highlightId ? Number(highlightId) : null;

  useEffect(() => {
    if (!selectedInstitutionId) return;
    if (initialInstitutionId !== selectedInstitutionId) return;
    if (initialStudents.length === 0) return;
    seedStudentsForInstitution(selectedInstitutionId, initialStudents);
  }, [
    initialInstitutionId,
    initialStudents,
    seedStudentsForInstitution,
    selectedInstitutionId
  ]);

  useEffect(() => {
    if (!selectedInstitutionId) return;
    if (initialInstitutionId !== selectedInstitutionId) return;
    if (initialInsights.length > 0) {
      seedInsightsForInstitution(selectedInstitutionId, initialInsights);
    }
  }, [
    initialInstitutionId,
    initialInsights,
    seedInsightsForInstitution,
    selectedInstitutionId
  ]);

  const refreshInsights = useCallback(() => {
    if (!selectedInstitutionId) return;
    void loadInsightsForInstitution(selectedInstitutionId, { force: true });
  }, [loadInsightsForInstitution, selectedInstitutionId]);

  useEffect(() => {
    refreshInsights();
  }, [refreshInsights]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const scanPending = () => {
      let pending = false;
      for (let i = 0; i < window.sessionStorage.length; i += 1) {
        const key = window.sessionStorage.key(i);
        if (key && key.startsWith('insight-pending:')) {
          const raw = window.sessionStorage.getItem(key);
          const startedAt = raw ? Number(raw) : NaN;
          if (Number.isFinite(startedAt) && Date.now() - startedAt > 5 * 60 * 1000) {
            window.sessionStorage.removeItem(key);
            continue;
          }
          pending = true;
          break;
        }
      }
      setHasPending(pending);
    };

    scanPending();
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        scanPending();
      }
    };

    window.addEventListener('focus', scanPending);
    document.addEventListener('visibilitychange', handleVisibility);
    window.addEventListener('insight:pending-change', scanPending);
    return () => {
      window.removeEventListener('focus', scanPending);
      document.removeEventListener('visibilitychange', handleVisibility);
      window.removeEventListener('insight:pending-change', scanPending);
    };
  }, []);

  useEffect(() => {
    if (!hasPending) return;
    const interval = window.setInterval(() => {
      refreshInsights();
    }, 3000);
    return () => window.clearInterval(interval);
  }, [hasPending, refreshInsights]);

  const students = useMemo(() => {
    if (selectedInstitutionId && selectedInstitutionId !== initialInstitutionId) {
      return contextStudents;
    }
    return contextStudents.length > 0 ? contextStudents : initialStudents;
  }, [contextStudents, initialInstitutionId, initialStudents, selectedInstitutionId]);

  const insightsSource = useMemo(() => {
    if (selectedInstitutionId && selectedInstitutionId !== initialInstitutionId) {
      return insights;
    }
    return insights.length > 0 ? insights : initialInsights;
  }, [initialInsights, initialInstitutionId, insights, selectedInstitutionId]);

  const latestByStudent = useMemo(() => {
    const map = new Map<number, (typeof insights)[number]>();
    for (const insight of insightsSource) {
      if (!map.has(insight.studentDatabaseId)) {
        map.set(insight.studentDatabaseId, insight);
      }
    }
    return map;
  }, [insightsSource]);

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
        onRefresh={refreshInsights}
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
