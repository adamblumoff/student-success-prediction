'use client';

import { useState } from 'react';

const ranges = ['7d', '30d', '90d', 'Term'] as const;

type Range = (typeof ranges)[number];

export default function TimeRangeToggle() {
  const [active, setActive] = useState<Range>('30d');

  return (
    <div className="flex items-center gap-3 rounded-full border border-ink-700/60 bg-ink-900/80 p-1 text-xs font-semibold text-ink-300">
      {ranges.map((range) => (
        <button
          key={range}
          type="button"
          onClick={() => setActive(range)}
          className={`rounded-full px-4 py-2 ${
            active === range ? 'bg-ink-700/70 text-ink-50' : 'hover:bg-ink-800/60'
          }`}
        >
          {range}
        </button>
      ))}
    </div>
  );
}
