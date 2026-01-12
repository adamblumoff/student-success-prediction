'use client';

import { useEffect, useState, useTransition } from 'react';
import { updateInterventionStatus, deleteIntervention } from '@/lib/actions/interventions';
import { cn } from '@/lib/cn';
import { useAppData } from '@/components/app-data-provider';

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

const statusTone = (status: string | null) => {
  if (status === 'completed') return 'badge-risk-low';
  if (status === 'active') return 'badge-risk-medium';
  return 'badge-risk-high';
};

export default function InterventionTable({ initialRows }: { initialRows: Row[] }) {
  const {
    selectedInstitutionId,
    markDashboardStatsStale,
    markInsightsStale,
    markInterventionsStale
  } = useAppData();
  const [rows, setRows] = useState(initialRows);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    setRows(initialRows);
  }, [initialRows]);

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
      if (selectedInstitutionId) {
        markDashboardStatsStale(selectedInstitutionId);
        markInsightsStale(selectedInstitutionId);
        markInterventionsStale(selectedInstitutionId);
      }
    });
  };

  const handleDelete = (id: number) => {
    startTransition(async () => {
      await deleteIntervention(id);
      setRows((prev) => prev.filter((row) => row.intervention.id !== id));
      if (selectedInstitutionId) {
        markDashboardStatsStale(selectedInstitutionId);
        markInsightsStale(selectedInstitutionId);
        markInterventionsStale(selectedInstitutionId);
      }
    });
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase text-ink-400">Active plans</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink-50 text-balance">
            Interventions
          </h2>
        </div>
        {isPending && <span className="text-xs text-ink-500">Updating...</span>}
      </div>
      <div className="mt-6 space-y-3">
        {rows.map((row) => (
          <div
            key={row.intervention.id}
            className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-ink-100">{row.intervention.title}</p>
                <p className="text-xs text-ink-400">
                  {row.student?.name ?? `Student ${row.student?.studentId ?? ''}`} ·{' '}
                  {row.intervention.interventionType}
                </p>
              </div>
              <span className={cn('badge', statusTone(row.intervention.status))}>
                {row.intervention.status ?? 'planned'}
              </span>
            </div>
            <div className="mt-3 flex flex-wrap gap-3 text-xs text-ink-400 tabular-nums">
              <span>Priority: {row.intervention.priority ?? 'medium'}</span>
              <span>Assigned: {row.intervention.assignedTo ?? 'Unassigned'}</span>
              <span>
                Due:{' '}
                {row.intervention.dueDate
                  ? new Date(row.intervention.dueDate).toLocaleDateString()
                  : '-'}
              </span>
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <select
                value={row.intervention.status ?? 'planned'}
                onChange={(event) => handleStatusChange(row.intervention.id, event.target.value)}
                className="select-field rounded-full border border-ink-700/60 bg-ink-900/60 px-3 py-2 text-xs text-ink-200"
              >
                <option value="planned">Planned</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
              </select>
              <button
                type="button"
                onClick={() => handleStatusChange(row.intervention.id, 'completed')}
                className="rounded-full border border-ink-700/60 px-3 py-2 text-xs text-ink-200"
              >
                Mark done
              </button>
              <button
                type="button"
                className="rounded-full border border-ink-700/60 px-3 py-2 text-xs text-ink-400"
                disabled
              >
                Edit
              </button>
              <button
                type="button"
                className="rounded-full border border-ink-700/60 px-3 py-2 text-xs text-ink-400"
                disabled
              >
                Duplicate
              </button>
              <button
                type="button"
                onClick={() => handleDelete(row.intervention.id)}
                className="rounded-full border border-ink-700/60 px-3 py-2 text-xs text-rose-300"
              >
                Remove
              </button>
            </div>
          </div>
        ))}
        {rows.length === 0 && (
          <div className="rounded-2xl border border-dashed border-ink-700/60 p-6 text-sm text-ink-400 text-pretty">
            No interventions yet. Add your first plan on the left and keep the team in sync.
          </div>
        )}
      </div>
    </div>
  );
}
