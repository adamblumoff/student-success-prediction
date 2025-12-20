'use client';

import { useState, useTransition } from 'react';
import { getQuickInsight } from '@/lib/actions/insights';

export default function InsightCard({
  studentId,
  name,
  highlight
}: {
  studentId: number;
  name: string | null;
  highlight?: boolean;
}) {
  const [isPending, startTransition] = useTransition();
  const [html, setHtml] = useState<string | null>(null);
  const [cached, setCached] = useState<boolean | null>(null);

  const handleClick = () => {
    startTransition(async () => {
      const result = await getQuickInsight(studentId);
      setHtml(result.formattedHtml);
      setCached(result.cached);
    });
  };

  return (
    <div className={`card ${highlight ? 'ring-2 ring-sage-400' : ''}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-lg font-semibold text-ink-900">{name ?? `Student ${studentId}`}</p>
          <p className="text-xs text-ink-500">Quick GPT insight</p>
        </div>
        <button
          type="button"
          onClick={handleClick}
          className="rounded-full border border-ink-200 px-4 py-2 text-xs font-semibold"
        >
          {isPending ? 'Generating...' : 'Generate'}
        </button>
      </div>
      {cached !== null && (
        <p className="mt-3 text-xs text-ink-500">
          {cached ? 'Loaded from cache' : 'Fresh insight generated'}
        </p>
      )}
      {html && (
        <div
          className="mt-4 rounded-2xl border border-ink-100 bg-ink-50 p-4 text-sm text-ink-700"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      )}
    </div>
  );
}
