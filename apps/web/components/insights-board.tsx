'use client';

import { useMemo, useState } from 'react';
import InsightCard from '@/components/insight-card';

export type InsightsStudent = {
  id: number;
  name: string | null;
  riskCategory: string | null;
  riskScore: number | null;
  confidenceScore: number | null;
  predictionDate: string | null;
  cachedInsightHtml?: string | null;
  cachedInsightAt?: string | null;
  cachedInsightRisk?: string | null;
};

export default function InsightsBoard({
  students,
  highlightId,
  onRefresh
}: {
  students: InsightsStudent[];
  highlightId: number | null;
  onRefresh?: () => void;
}) {
  const [query, setQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');
  const [bulkQueue, setBulkQueue] = useState<number[]>([]);

  const topRiskIds = useMemo(() => {
    const sorted = [...students]
      .filter((student) => student.riskScore !== null)
      .sort((a, b) => (b.riskScore ?? 0) - (a.riskScore ?? 0))
      .slice(0, 10);
    return new Set(sorted.map((student) => student.id));
  }, [students]);

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return students.filter((student) => {
      const name = student.name?.toLowerCase() ?? '';
      const matchesQuery = !normalizedQuery || name.includes(normalizedQuery);
      const normalizedRisk = student.riskCategory?.toLowerCase() ?? '';
      const matchesRisk =
        riskFilter === 'all' ||
        (riskFilter === 'high' && normalizedRisk.includes('high')) ||
        (riskFilter === 'moderate' &&
          (normalizedRisk.includes('moderate') || normalizedRisk.includes('medium'))) ||
        (riskFilter === 'low' && normalizedRisk.includes('low')) ||
        (riskFilter === 'unknown' && !normalizedRisk);

      return matchesQuery && matchesRisk;
    });
  }, [students, query, riskFilter]);

  const handleBulkGenerate = () => {
    const count = topRiskIds.size;
    if (count === 0) return;
    setBulkQueue(Array.from(topRiskIds));
  };

  const handleGenerated = (fromBulk: boolean) => {
    if (!fromBulk) return;
    setBulkQueue((prev) => (prev.length > 0 ? prev.slice(1) : prev));
  };

  const bulkActiveId = bulkQueue[0] ?? null;
  const bulkRemaining = bulkQueue.length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-ink-700/60 bg-ink-900/80 px-5 py-4">
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <input
            type="search"
            placeholder="Search students"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="h-10 w-64 rounded-full border border-ink-700/60 bg-ink-950/60 px-4 text-sm text-ink-100"
          />
          <select
            value={riskFilter}
            onChange={(event) => setRiskFilter(event.target.value)}
            className="select-field h-10 rounded-full border border-ink-700/60 bg-ink-950/60 px-4 text-sm text-ink-100"
          >
            <option value="all">All risk</option>
            <option value="high">High risk</option>
            <option value="moderate">Moderate risk</option>
            <option value="low">Low risk</option>
            <option value="unknown">Unknown</option>
          </select>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleBulkGenerate}
            className="rounded-full bg-sage-500 px-5 py-2 text-xs font-semibold text-slate-950"
          >
            Generate for top 10 high-risk
          </button>
          {bulkRemaining > 0 && (
            <span className="text-xs text-ink-400">Generating {bulkRemaining}...</span>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {filtered.map((student) => (
          <InsightCard
            key={student.id}
            studentId={student.id}
            name={student.name}
            highlight={highlightId === student.id}
            riskCategory={student.riskCategory}
            confidenceScore={student.confidenceScore}
            predictionDate={student.predictionDate}
            initialHtml={student.cachedInsightHtml ?? null}
            initialCached={Boolean(student.cachedInsightHtml)}
            initialGeneratedAt={student.cachedInsightAt ?? null}
            bulkActiveId={bulkActiveId}
            onGenerated={handleGenerated}
            onRefresh={onRefresh}
          />
        ))}
      </div>
    </div>
  );
}
