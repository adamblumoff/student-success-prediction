'use client';

import { useEffect, useMemo, useState } from 'react';
import { updateInterventionDetails, deleteIntervention } from '@/lib/actions/interventions';

const formatDateInput = (value: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toISOString().slice(0, 10);
};

type StudentInfo = {
  id: number;
  name: string | null;
  studentId: string;
  gradeLevel: string | null;
  enrollmentStatus: string | null;
};

type InterventionRow = {
  id: number;
  title: string;
  interventionType: string;
  description: string | null;
  status: string | null;
  priority: string | null;
  assignedTo: string | null;
  dueDate: string | null;
  createdAt: string | null;
};

export default function StudentInterventionsModal({
  studentId,
  open,
  onClose
}: {
  studentId: number | null;
  open: boolean;
  onClose: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [student, setStudent] = useState<StudentInfo | null>(null);
  const [rows, setRows] = useState<InterventionRow[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState<Partial<InterventionRow>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open || !studentId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/students/${studentId}/interventions`, {
      credentials: 'same-origin',
      cache: 'no-store'
    })
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({ error: 'Failed to load' }));
          throw new Error(body.error ?? 'Failed to load');
        }
        return res.json();
      })
      .then((data) => {
        setStudent(data.student);
        setRows(
          data.interventions.map((row: InterventionRow) => ({
            ...row,
            dueDate: row.dueDate ? new Date(row.dueDate).toISOString() : null,
            createdAt: row.createdAt ? new Date(row.createdAt).toISOString() : null
          }))
        );
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [open, studentId]);

  const startEdit = (row: InterventionRow) => {
    setEditingId(row.id);
    setDraft({
      title: row.title,
      interventionType: row.interventionType,
      description: row.description ?? '',
      status: row.status ?? 'planned',
      priority: row.priority ?? 'medium',
      assignedTo: row.assignedTo ?? '',
      dueDate: row.dueDate ?? ''
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setDraft({});
  };

  const saveEdit = async (rowId: number) => {
    if (!student) return;
    setSaving(true);
    try {
      const updated = await updateInterventionDetails(rowId, {
        title: String(draft.title ?? '').trim(),
        interventionType: String(draft.interventionType ?? '').trim(),
        description: String(draft.description ?? '').trim(),
        priority: String(draft.priority ?? '').trim(),
        status: String(draft.status ?? '').trim(),
        assignedTo: String(draft.assignedTo ?? '').trim(),
        dueDate: String(draft.dueDate ?? '').trim() || null
      });
      if (updated) {
        setRows((prev) =>
          prev.map((row) =>
            row.id === rowId
              ? {
                  ...row,
                  title: updated.title,
                  interventionType: updated.interventionType,
                  description: updated.description,
                  status: updated.status,
                  priority: updated.priority,
                  assignedTo: updated.assignedTo,
                  dueDate: updated.dueDate ? new Date(updated.dueDate).toISOString() : null
                }
              : row
          )
        );
      }
      cancelEdit();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (rowId: number) => {
    if (!confirm('Delete this intervention?')) return;
    try {
      await deleteIntervention(rowId);
      setRows((prev) => prev.filter((row) => row.id !== rowId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  const header = useMemo(() => {
    if (!student) return 'Student interventions';
    return `${student.name ?? `Student ${student.studentId}`} · Grade ${student.gradeLevel ?? '-'}`;
  }, [student]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/70 px-6 pt-[calc(env(safe-area-inset-top)+1.5rem)] pb-[calc(env(safe-area-inset-bottom)+1.5rem)]">
      <div className="w-full max-w-4xl rounded-3xl border border-ink-700/60 bg-ink-900/95 p-6 shadow-2xl">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase text-ink-400">Student insights</p>
            <h2 className="mt-2 text-2xl font-semibold text-ink-50 text-balance">{header}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-200"
          >
            Close
          </button>
        </div>

        {loading && <p className="mt-6 text-sm text-ink-400">Loading interventions...</p>}
        {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}

        {!loading && rows.length === 0 && (
          <div className="mt-6 rounded-2xl border border-dashed border-ink-700/60 p-6 text-sm text-ink-400">
            No interventions yet for this student.
          </div>
        )}

        <div className="mt-6 space-y-4">
          {rows.map((row) => (
            <div
              key={row.id}
              className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4"
            >
              {editingId === row.id ? (
                <div className="space-y-3 text-sm text-ink-200">
                  <div className="grid gap-3 md:grid-cols-2">
                    <label className="flex flex-col gap-1">
                      Title
                      <input
                        value={String(draft.title ?? '')}
                        onChange={(event) => setDraft((prev) => ({ ...prev, title: event.target.value }))}
                        className="rounded-2xl border border-ink-700/60 bg-ink-900/70 p-2"
                      />
                    </label>
                    <label className="flex flex-col gap-1">
                      Type
                      <input
                        value={String(draft.interventionType ?? '')}
                        onChange={(event) =>
                          setDraft((prev) => ({ ...prev, interventionType: event.target.value }))
                        }
                        className="rounded-2xl border border-ink-700/60 bg-ink-900/70 p-2"
                      />
                    </label>
                  </div>
                  <label className="flex flex-col gap-1">
                    Description
                    <textarea
                      rows={3}
                      value={String(draft.description ?? '')}
                      onChange={(event) =>
                        setDraft((prev) => ({ ...prev, description: event.target.value }))
                      }
                      className="rounded-2xl border border-ink-700/60 bg-ink-900/70 p-2"
                    />
                  </label>
                  <div className="grid gap-3 md:grid-cols-3">
                    <label className="flex flex-col gap-1">
                      Status
                      <select
                        value={String(draft.status ?? '')}
                        onChange={(event) => setDraft((prev) => ({ ...prev, status: event.target.value }))}
                        className="select-field rounded-2xl border border-ink-700/60 bg-ink-900/70 p-2"
                      >
                        <option value="planned">Planned</option>
                        <option value="active">Active</option>
                        <option value="completed">Completed</option>
                      </select>
                    </label>
                    <label className="flex flex-col gap-1">
                      Priority
                      <select
                        value={String(draft.priority ?? '')}
                        onChange={(event) =>
                          setDraft((prev) => ({ ...prev, priority: event.target.value }))
                        }
                        className="select-field rounded-2xl border border-ink-700/60 bg-ink-900/70 p-2"
                      >
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                    </label>
                    <label className="flex flex-col gap-1">
                      Due date
                      <input
                        type="date"
                        value={formatDateInput(String(draft.dueDate ?? ''))}
                        onChange={(event) =>
                          setDraft((prev) => ({ ...prev, dueDate: event.target.value }))
                        }
                        className="rounded-2xl border border-ink-700/60 bg-ink-900/70 p-2"
                      />
                    </label>
                  </div>
                  <label className="flex flex-col gap-1">
                    Assigned to
                    <input
                      value={String(draft.assignedTo ?? '')}
                      onChange={(event) =>
                        setDraft((prev) => ({ ...prev, assignedTo: event.target.value }))
                      }
                      className="rounded-2xl border border-ink-700/60 bg-ink-900/70 p-2"
                    />
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => saveEdit(row.id)}
                      className="rounded-full bg-sage-500 px-4 py-2 text-xs font-semibold text-slate-950"
                      disabled={saving}
                    >
                      {saving ? 'Saving...' : 'Save'}
                    </button>
                    <button
                      type="button"
                      onClick={cancelEdit}
                      className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-200"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-ink-50">{row.title}</p>
                    <p className="text-xs text-ink-400">
                      {row.interventionType} · {row.status ?? 'planned'} · Priority{' '}
                      {row.priority ?? 'medium'}
                    </p>
                    {row.description && (
                      <p className="mt-2 text-xs text-ink-300">{row.description}</p>
                    )}
                    <div className="mt-2 flex flex-wrap gap-3 text-xs text-ink-400">
                      <span>Assigned: {row.assignedTo ?? 'Unassigned'}</span>
                      <span>
                        Due:{' '}
                        {row.dueDate ? new Date(row.dueDate).toLocaleDateString() : '—'}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => startEdit(row)}
                      className="rounded-full border border-ink-700/60 px-3 py-2 text-xs font-semibold text-ink-200"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(row.id)}
                      className="rounded-full border border-rose-500/60 px-3 py-2 text-xs font-semibold text-rose-300"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
