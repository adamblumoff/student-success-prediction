'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/cn';
const STORAGE_PREFIX = 'insight-prefill:';
const PENDING_PREFIX = 'insight-pending:';

const toPlainText = (value: string) => {
  if (typeof window === 'undefined') return value;
  const wrapper = document.createElement('div');
  wrapper.innerHTML = value;
  return (wrapper.textContent || wrapper.innerText || '').trim();
};

const extractInsightLines = (value: string) => {
  const stripTags = (input: string) =>
    input.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
  const matches = Array.from(value.matchAll(/<li>(.*?)<\/li>/gis)).map((match) =>
    stripTags(match[1])
  );
  const lines = matches.length
    ? matches
    : value.split(/\n+/).map((line) => stripTags(line));
  return lines.filter(Boolean).slice(0, 3);
};

type Props = {
  studentId: number;
  name: string | null;
  highlight?: boolean;
  riskCategory?: string | null;
  confidenceScore?: number | null;
  predictionDate?: string | null;
  initialHtml?: string | null;
  initialCached?: boolean;
  initialGeneratedAt?: string | null;
  bulkActiveId?: number | null;
  onGenerated?: (fromBulk: boolean) => void;
  onRefresh?: () => void;
};

export default function InsightCard({
  studentId,
  name,
  highlight,
  riskCategory,
  confidenceScore,
  predictionDate,
  initialHtml,
  initialCached,
  initialGeneratedAt,
  bulkActiveId,
  onGenerated,
  onRefresh
}: Props) {
  const router = useRouter();
  const [isGenerating, setIsGenerating] = useState(false);
  const [html, setHtml] = useState<string | null>(initialHtml ?? null);
  const [cached, setCached] = useState<boolean | null>(
    initialCached === undefined ? null : initialCached
  );
  const [generatedAt, setGeneratedAt] = useState<Date | null>(
    initialGeneratedAt ? new Date(initialGeneratedAt) : null
  );

  const pendingKey = useMemo(() => `${PENDING_PREFIX}${studentId}`, [studentId]);

  const handleClick = useCallback(
    async (fromBulk = false) => {
      if (isGenerating) return;
      if (typeof window !== 'undefined') {
        window.sessionStorage.setItem(pendingKey, String(Date.now()));
        window.dispatchEvent(new Event('insight:pending-change'));
      }
      setIsGenerating(true);
      try {
        const response = await fetch('/api/insights/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ studentId })
        });
        if (!response.ok) return;
        const result = (await response.json()) as {
          cached: boolean;
          formattedHtml: string | null;
          riskLevel: string | null;
        };
        setHtml(result.formattedHtml);
        setCached(result.cached);
        setGeneratedAt(new Date());
      } finally {
        setIsGenerating(false);
        if (typeof window !== 'undefined') {
          window.sessionStorage.removeItem(pendingKey);
          window.dispatchEvent(new Event('insight:pending-change'));
        }
        onGenerated?.(fromBulk);
      }
    },
    [isGenerating, onGenerated, pendingKey, studentId]
  );

  const handleCopy = () => {
    const token = `${studentId}-${Date.now()}`;
    const payload = {
      studentId,
      studentName: name,
      title: 'Insight plan',
      interventionType: 'Insight plan',
      description: html ? toPlainText(html) : '',
      source: 'insight'
    };
    sessionStorage.setItem(`${STORAGE_PREFIX}${token}`, JSON.stringify(payload));
    router.push(`/interventions?prefill=${token}`);
  };

  useEffect(() => {
    if (bulkActiveId !== studentId) return;
    handleClick(true);
  }, [bulkActiveId, handleClick, studentId]);

  useEffect(() => {
    if (!initialHtml) return;
    setHtml(initialHtml);
    setCached(initialCached === undefined ? null : initialCached);
    setGeneratedAt(initialGeneratedAt ? new Date(initialGeneratedAt) : null);
    if (isGenerating) {
      setIsGenerating(false);
      if (typeof window !== 'undefined') {
        window.sessionStorage.removeItem(pendingKey);
        window.dispatchEvent(new Event('insight:pending-change'));
      }
    }
  }, [initialCached, initialGeneratedAt, initialHtml, isGenerating, pendingKey]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!window.sessionStorage.getItem(pendingKey)) return;
    if (initialHtml) {
      window.sessionStorage.removeItem(pendingKey);
      window.dispatchEvent(new Event('insight:pending-change'));
      return;
    }
    setIsGenerating(true);
  }, [initialHtml, pendingKey]);

  return (
    <div className={cn('card', highlight && 'ring-2 ring-sage-400')}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-lg font-semibold text-ink-50 text-balance">
            {name ?? `Student ${studentId}`}
          </p>
          <p className="text-xs text-ink-400">Quick GPT insight</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {riskCategory && (
            <span
              className={cn(
                'badge',
                riskCategory.toLowerCase().includes('high')
                  ? 'badge-risk-high'
                  : riskCategory.toLowerCase().includes('moderate') ||
                      riskCategory.toLowerCase().includes('medium')
                    ? 'badge-risk-medium'
                    : 'badge-risk-low'
              )}
            >
              {riskCategory}
            </span>
          )}
          <button
            type="button"
            onClick={() => void handleClick(false)}
            className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-200"
          >
            {isGenerating ? 'Generating...' : 'Generate'}
          </button>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-ink-400 tabular-nums">
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
        <div className="mt-4 rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4 text-sm text-ink-200">
          <ul className="list-disc space-y-2 pl-5">
            {extractInsightLines(html).map((line, index) => (
              <li key={`${studentId}-${index}`}>{line}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-200"
          disabled={!html}
        >
          Copy to intervention plan
        </button>
      </div>
    </div>
  );
}
