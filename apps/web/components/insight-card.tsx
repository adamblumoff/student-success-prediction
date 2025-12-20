'use client';

import { useEffect, useRef, useState, useTransition } from 'react';
import Link from 'next/link';
import { getQuickInsight } from '@/lib/actions/insights';

type Props = {
  studentId: number;
  name: string | null;
  highlight?: boolean;
  riskCategory?: string | null;
  confidenceScore?: number | null;
  predictionDate?: string | null;
  bulkToken?: number;
  autoGenerate?: boolean;
  onGenerated?: (fromBulk: boolean) => void;
};

export default function InsightCard({
  studentId,
  name,
  highlight,
  riskCategory,
  confidenceScore,
  predictionDate,
  bulkToken,
  autoGenerate,
  onGenerated
}: Props) {
  const [isPending, startTransition] = useTransition();
  const [html, setHtml] = useState<string | null>(null);
  const [cached, setCached] = useState<boolean | null>(null);
  const [generatedAt, setGeneratedAt] = useState<Date | null>(null);
  const lastBulkToken = useRef<number | null>(null);

  const handleClick = (fromBulk = false) => {
    startTransition(async () => {
      const result = await getQuickInsight(studentId);
      setHtml(result.formattedHtml);
      setCached(result.cached);
      setGeneratedAt(new Date());
      onGenerated?.(fromBulk);
    });
  };

  useEffect(() => {
    if (!autoGenerate || !bulkToken) return;
    if (lastBulkToken.current === bulkToken) return;
    lastBulkToken.current = bulkToken;
    handleClick(true);
  }, [autoGenerate, bulkToken]);

  return (
    <div className={`card ${highlight ? 'ring-2 ring-sage-400' : ''}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-lg font-semibold text-ink-50">{name ?? `Student ${studentId}`}</p>
          <p className="text-xs text-ink-400">Quick GPT insight</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {riskCategory && (
            <span
              className={`badge ${
                riskCategory.toLowerCase().includes('high')
                  ? 'badge-risk-high'
                  : riskCategory.toLowerCase().includes('moderate') ||
                      riskCategory.toLowerCase().includes('medium')
                    ? 'badge-risk-medium'
                    : 'badge-risk-low'
              }`}
            >
              {riskCategory}
            </span>
          )}
          <button
            type="button"
            onClick={() => handleClick(false)}
            className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-200"
          >
            {isPending ? 'Generating...' : 'Generate'}
          </button>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-ink-400">
        <span>Signals: GPA, attendance, enrollment status</span>
        <span>•</span>
        <span>
          Confidence:{' '}
          {confidenceScore !== null && confidenceScore !== undefined
            ? `${Math.round(confidenceScore * 100)}%`
            : 'Experimental'}
        </span>
        <span>•</span>
        <span>
          Risk updated:{' '}
          {predictionDate ? new Date(predictionDate).toLocaleDateString() : '—'}
        </span>
      </div>

      {cached !== null && (
        <p className="mt-3 text-xs text-ink-400">
          {cached ? 'Loaded from cache' : 'Fresh insight generated'}
          {generatedAt ? ` · ${generatedAt.toLocaleTimeString()}` : ''}
        </p>
      )}

      {html && (
        <div
          className="mt-4 rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4 text-sm text-ink-200"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <Link
          href="/interventions"
          className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-200"
        >
          Copy to intervention plan
        </Link>
      </div>
    </div>
  );
}
