'use client';

import { useState, useTransition } from 'react';
import { updateInterventionStatus, deleteIntervention } from '@/lib/actions/interventions';

type Row = {
  intervention: {
    id: number;
    title: string;
    interventionType: string;
    status: string | null;
    priority: string | null;
    assignedTo: string | null;
    dueDate: string | null;
  };
  student: {
    name: string | null;
    studentId: string;
  } | null;
};

export default function InterventionTable({ initialRows }: { initialRows: Row[] }) {
  const [rows, setRows] = useState(initialRows);
  const [isPending, startTransition] = useTransition();

  const handleStatusChange = (id: number, status: string) => {
    startTransition(async () => {
      await updateInterventionStatus(id, status);
      setRows((prev) =>
        prev.map((row) =>
          row.intervention.id === id
            ? { ...row, intervention: { ...row.intervention, status } }
            : row
        )
      );
    });
  };

  const handleDelete = (id: number) => {
    startTransition(async () => {
      await deleteIntervention(id);
      setRows((prev) => prev.filter((row) => row.intervention.id !== id));
    });
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-ink-400">Active plans</p>
          <h2 className="mt-2 text-2xl font-semibold">Interventions</h2>
        </div>
        {isPending && <span className="text-xs text-ink-500">Updating...</span>}
      </div>
      <div className="mt-6 space-y-3">
        {rows.map((row) => (
          <div key={row.intervention.id} className="rounded-2xl border border-ink-100 bg-white p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-ink-800">{row.intervention.title}</p>
                <p className="text-xs text-ink-500">
                  {row.student?.name ?? `Student ${row.student?.studentId ?? ''}`} -{' '}
                  {row.intervention.interventionType}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={row.intervention.status ?? 'planned'}
                  onChange={(event) => handleStatusChange(row.intervention.id, event.target.value)}
                  className="rounded-full border border-ink-200 px-3 py-1 text-xs"
                >
                  <option value="planned">Planned</option>
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                </select>
                <button
                  type="button"
                  onClick={() => handleDelete(row.intervention.id)}
                  className="rounded-full border border-ink-200 px-3 py-1 text-xs"
                >
                  Remove
                </button>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-3 text-xs text-ink-500">
              <span>Priority: {row.intervention.priority ?? 'medium'}</span>
              <span>Assigned: {row.intervention.assignedTo ?? 'Unassigned'}</span>
              <span>
                Due:{' '}
                {row.intervention.dueDate
                  ? new Date(row.intervention.dueDate).toLocaleDateString()
                  : '-'}
              </span>
            </div>
          </div>
        ))}
        {rows.length === 0 && (
          <div className="rounded-2xl border border-dashed border-ink-200 p-6 text-sm text-ink-500">
            No interventions yet. Add your first plan on the left.
          </div>
        )}
      </div>
    </div>
  );
}
