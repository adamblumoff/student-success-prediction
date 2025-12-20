'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { deleteStudentsAction } from '@/lib/actions/students';

export type StudentWithRisk = {
  id: number;
  studentId: string;
  name: string | null;
  gradeLevel: string | null;
  currentGpa: number | null;
  attendanceRate: number | null;
  enrollmentStatus: string | null;
  lastActivity: string | null;
  activeInterventions: number | null;
  riskCategory: string | null;
  riskScore: number | null;
  confidenceScore: number | null;
  predictionDate: string | null;
};

type ViewMode = 'cards' | 'table';

type RiskFilter = 'all' | 'high' | 'moderate' | 'low' | 'unknown';

type SortMode = 'risk-desc' | 'risk-asc' | 'name' | 'gpa-desc';

const getRiskTone = (riskCategory: string | null) => {
  const normalized = riskCategory?.toLowerCase() ?? '';
  if (normalized.includes('high')) return 'badge-risk-high';
  if (normalized.includes('moderate') || normalized.includes('medium')) return 'badge-risk-medium';
  if (normalized.includes('low')) return 'badge-risk-low';
  return 'badge-risk-medium';
};

const getRiskLabel = (riskCategory: string | null) => {
  if (!riskCategory) return 'Unknown';
  return riskCategory;
};

export default function StudentRoster({ students }: { students: StudentWithRisk[] }) {
  const [roster, setRoster] = useState(students);
  const [query, setQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState<RiskFilter>('all');
  const [gradeFilter, setGradeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortMode, setSortMode] = useState<SortMode>('risk-desc');
  const [viewMode, setViewMode] = useState<ViewMode>('cards');
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [isDeleting, setIsDeleting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    setRoster(students);
  }, [students]);

  const grades = useMemo(() => {
    const unique = new Set(
      roster.map((student) => student.gradeLevel).filter((value): value is string => Boolean(value))
    );
    return Array.from(unique).sort();
  }, [roster]);

  const statuses = useMemo(() => {
    const unique = new Set(
      roster
        .map((student) => student.enrollmentStatus)
        .filter((value): value is string => Boolean(value))
    );
    return Array.from(unique).sort();
  }, [roster]);

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    const matchesRisk = (riskCategory: string | null) => {
      if (riskFilter === 'all') return true;
      const normalized = riskCategory?.toLowerCase() ?? '';
      if (riskFilter === 'high') return normalized.includes('high');
      if (riskFilter === 'moderate')
        return normalized.includes('moderate') || normalized.includes('medium');
      if (riskFilter === 'low') return normalized.includes('low');
      return !normalized;
    };

    const filteredStudents = roster.filter((student) => {
      const name = student.name?.toLowerCase() ?? '';
      const id = student.studentId?.toLowerCase() ?? '';
      const matchesQuery =
        !normalizedQuery || name.includes(normalizedQuery) || id.includes(normalizedQuery);

      const matchesGrade = gradeFilter === 'all' || student.gradeLevel === gradeFilter;
      const matchesStatus = statusFilter === 'all' || student.enrollmentStatus === statusFilter;

      return matchesQuery && matchesRisk(student.riskCategory) && matchesGrade && matchesStatus;
    });

    const sortedStudents = [...filteredStudents].sort((a, b) => {
      if (sortMode === 'name') {
        return (a.name ?? '').localeCompare(b.name ?? '');
      }
      if (sortMode === 'gpa-desc') {
        return (b.currentGpa ?? 0) - (a.currentGpa ?? 0);
      }
      const riskA = a.riskScore ?? 0;
      const riskB = b.riskScore ?? 0;
      return sortMode === 'risk-desc' ? riskB - riskA : riskA - riskB;
    });

    return sortedStudents;
  }, [roster, query, riskFilter, gradeFilter, statusFilter, sortMode]);

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === filtered.length) {
      setSelected(new Set());
      return;
    }
    setSelected(new Set(filtered.map((student) => student.id)));
  };

  const selectionCount = selected.size;
  const selectedWithActive = filtered.filter(
    (student) => selected.has(student.id) && (student.activeInterventions ?? 0) > 0
  );
  const activeInterventionsCount = selectedWithActive.reduce(
    (total, student) => total + (student.activeInterventions ?? 0),
    0
  );

  const handleDelete = async () => {
    if (selectionCount === 0 || isDeleting) return;
    const warning =
      activeInterventionsCount > 0
        ? `Warning: ${activeInterventionsCount} active intervention(s) are linked to the selected students. These will be deleted too.`
        : 'This will permanently delete the selected students and their predictions/interventions.';
    const confirmed = window.confirm(`${warning}\n\nContinue with delete?`);
    if (!confirmed) return;

    setIsDeleting(true);
    setStatusMessage(null);
    try {
      const result = await deleteStudentsAction(Array.from(selected));
      setRoster((prev) => prev.filter((student) => !result.deletedIds.includes(student.id)));
      setSelected(new Set());
      setStatusMessage(`Deleted ${result.deletedCount} student(s).`);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Delete failed.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-ink-700/60 bg-ink-900/80 px-5 py-4">
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <input
            type="search"
            placeholder="Search by name or student ID"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="h-10 w-64 rounded-full border border-ink-700/60 bg-ink-950/60 px-4 text-sm text-ink-100"
          />
          <select
            value={riskFilter}
            onChange={(event) => setRiskFilter(event.target.value as RiskFilter)}
            className="h-10 rounded-full border border-ink-700/60 bg-ink-950/60 px-4 text-sm text-ink-100"
          >
            <option value="all">All risk</option>
            <option value="high">High risk</option>
            <option value="moderate">Moderate risk</option>
            <option value="low">Low risk</option>
            <option value="unknown">Unknown</option>
          </select>
          <select
            value={gradeFilter}
            onChange={(event) => setGradeFilter(event.target.value)}
            className="h-10 rounded-full border border-ink-700/60 bg-ink-950/60 px-4 text-sm text-ink-100"
          >
            <option value="all">All grades</option>
            {grades.map((grade) => (
              <option key={grade} value={grade}>
                Grade {grade}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="h-10 rounded-full border border-ink-700/60 bg-ink-950/60 px-4 text-sm text-ink-100"
          >
            <option value="all">All status</option>
            {statuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
          <select
            value={sortMode}
            onChange={(event) => setSortMode(event.target.value as SortMode)}
            className="h-10 rounded-full border border-ink-700/60 bg-ink-950/60 px-4 text-sm text-ink-100"
          >
            <option value="risk-desc">Highest risk</option>
            <option value="risk-asc">Lowest risk</option>
            <option value="name">Name A-Z</option>
            <option value="gpa-desc">Top GPA</option>
          </select>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-ink-700/60 bg-ink-950/60 p-1 text-xs font-semibold text-ink-300">
          <button
            type="button"
            onClick={() => setViewMode('cards')}
            className={`rounded-full px-4 py-2 ${
              viewMode === 'cards' ? 'bg-ink-700/70 text-ink-50' : 'hover:bg-ink-800/60'
            }`}
          >
            Cards
          </button>
          <button
            type="button"
            onClick={() => setViewMode('table')}
            className={`rounded-full px-4 py-2 ${
              viewMode === 'table' ? 'bg-ink-700/70 text-ink-50' : 'hover:bg-ink-800/60'
            }`}
          >
            Table
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-ink-700/60 bg-ink-900/60 px-5 py-4 text-sm text-ink-200">
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={filtered.length > 0 && selectionCount === filtered.length}
            onChange={toggleSelectAll}
            className="h-4 w-4 rounded border border-ink-600 bg-ink-950"
          />
          <span>{selectionCount} selected</span>
          <span className="text-ink-500">·</span>
          <span>{filtered.length} students</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="rounded-full border border-rose-500/60 px-4 py-2 text-xs font-semibold text-rose-300"
            onClick={handleDelete}
            disabled={selectionCount === 0 || isDeleting}
            aria-disabled={selectionCount === 0 || isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete selected'}
          </button>
          <button
            type="button"
            className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-300"
            disabled
          >
            Assign counselor
          </button>
          <button
            type="button"
            className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-300"
            disabled
          >
            Add intervention
          </button>
          <button
            type="button"
            className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-300"
            disabled
          >
            Export roster
          </button>
        </div>
        {statusMessage && <p className="text-xs text-ink-400">{statusMessage}</p>}
        {activeInterventionsCount > 0 && (
          <p className="text-xs text-amber-300">
            {activeInterventionsCount} active intervention(s) linked to selected students.
          </p>
        )}
      </div>

      {viewMode === 'cards' ? (
        <div className="grid gap-4 md:grid-cols-2">
          {filtered.map((student) => (
            <div key={student.id} className="card">
              <div className="flex items-start justify-between gap-3">
                <label className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={selected.has(student.id)}
                    onChange={() => toggleSelect(student.id)}
                    className="mt-1 h-4 w-4 rounded border border-ink-600 bg-ink-950"
                  />
                  <div>
                    <p className="text-lg font-semibold text-ink-50">
                      {student.name ?? `Student ${student.studentId}`}
                    </p>
                    <p className="text-sm text-ink-400">
                      Grade {student.gradeLevel ?? '-'} · GPA {student.currentGpa ?? '-'}
                    </p>
                  </div>
                </label>
                <div className="flex flex-col items-end gap-2">
                  <span className={`badge ${getRiskTone(student.riskCategory)}`}>
                    {getRiskLabel(student.riskCategory)}
                  </span>
                  {student.confidenceScore !== null && (
                    <span className="text-xs text-ink-400">
                      Confidence {Math.round(student.confidenceScore * 100)}%
                    </span>
                  )}
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-ink-400">
                <div>
                  Attendance:{' '}
                  {student.attendanceRate !== null
                    ? `${Math.round(student.attendanceRate * 100)}%`
                    : '-'}
                </div>
                <div>Status: {student.enrollmentStatus ?? 'active'}</div>
                <div>
                  Last activity:{' '}
                  {student.lastActivity
                    ? new Date(student.lastActivity).toLocaleDateString()
                    : '—'}
                </div>
                <div>
                  Risk updated:{' '}
                  {student.predictionDate
                    ? new Date(student.predictionDate).toLocaleDateString()
                    : '—'}
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  href={`/insights?student=${student.id}`}
                  className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-200"
                >
                  View insights
                </Link>
                <Link
                  href="/interventions"
                  className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-200"
                >
                  Add intervention
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="overflow-hidden rounded-3xl border border-ink-700/60 bg-ink-900/70">
          <table className="w-full text-left text-sm">
            <thead className="bg-ink-950/70 text-xs uppercase tracking-[0.25em] text-ink-500">
              <tr>
                <th className="px-4 py-3">Select</th>
                <th className="px-4 py-3">Student</th>
                <th className="px-4 py-3">Grade</th>
                <th className="px-4 py-3">Risk</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Attendance</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-800/60">
              {filtered.map((student) => (
                <tr key={student.id} className="text-ink-200">
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selected.has(student.id)}
                      onChange={() => toggleSelect(student.id)}
                      className="h-4 w-4 rounded border border-ink-600 bg-ink-950"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-semibold text-ink-50">
                      {student.name ?? `Student ${student.studentId}`}
                    </div>
                    <div className="text-xs text-ink-400">{student.studentId}</div>
                  </td>
                  <td className="px-4 py-3">{student.gradeLevel ?? '-'}</td>
                  <td className="px-4 py-3">
                    <span className={`badge ${getRiskTone(student.riskCategory)}`}>
                      {getRiskLabel(student.riskCategory)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {student.confidenceScore !== null
                      ? `${Math.round(student.confidenceScore * 100)}%`
                      : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {student.attendanceRate !== null
                      ? `${Math.round(student.attendanceRate * 100)}%`
                      : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/insights?student=${student.id}`}
                      className="rounded-full border border-ink-700/60 px-3 py-2 text-xs font-semibold text-ink-200"
                    >
                      Insights
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
