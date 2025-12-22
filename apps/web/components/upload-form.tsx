'use client';

import { useActionState } from 'react';
import { useFormStatus } from 'react-dom';
import { analyzeGradebookAction, type AnalyzeState } from '@/lib/actions/analyze';
import clsx from 'clsx';

const initialState: AnalyzeState = { status: 'idle' };

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      className={clsx(
        'rounded-full px-6 py-3 text-sm font-semibold text-slate-950',
        pending ? 'bg-ink-500' : 'bg-sage-500 hover:bg-sage-400'
      )}
      disabled={pending}
    >
      {pending ? 'Analyzing...' : 'Upload & generate risk'}
    </button>
  );
}

export default function UploadForm() {
  const [state, formAction] = useActionState(analyzeGradebookAction, initialState);

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.1fr]">
      <form action={formAction} className="card flex flex-col gap-6">
        <div>
          <p className="badge badge-risk-low">Gradebook analysis</p>
          <h2 className="mt-4 text-2xl font-semibold text-ink-50">Upload your latest CSV</h2>
          <p className="mt-2 text-sm text-ink-300">
            We&apos;ll send the gradebook to the ML service and hydrate your dashboard with
            fresh predictions.
          </p>
        </div>
        <div className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4 text-sm text-ink-200">
          <p className="text-xs uppercase tracking-[0.3em] text-ink-500">
            Required columns
          </p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {['student_id', 'name', 'grade_level', 'current_gpa', 'attendance_rate'].map(
              (column) => (
                <div key={column} className="rounded-xl border border-ink-700/50 px-3 py-2">
                  {column}
                </div>
              )
            )}
          </div>
          <a
            href="/templates/gradebook-template.csv"
            className="mt-4 inline-flex items-center gap-2 text-xs font-semibold text-sage-300"
          >
            Download CSV template
          </a>
        </div>
        <label className="flex flex-col gap-2 text-sm font-medium text-ink-200">
          Gradebook CSV
          <input
            type="file"
            name="file"
            accept=".csv"
            className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-sm text-ink-200 file:mr-4 file:rounded-full file:border-0 file:bg-ink-800 file:px-4 file:py-2 file:text-xs file:font-semibold file:text-ink-200"
            required
          />
        </label>
        <div className="flex flex-wrap items-center gap-4">
          <SubmitButton />
          {state.status === 'error' && (
            <span className="text-sm text-rose-300">{state.error}</span>
          )}
          {state.status === 'success' && (
            <span className="text-sm text-sage-200">Analysis complete.</span>
          )}
        </div>
        <div className="rounded-2xl border border-dashed border-ink-700/60 p-4 text-xs text-ink-400">
          After upload, we will validate your columns, preview the first 10 rows, and
          refresh risk predictions automatically.
        </div>
      </form>

      <div className="bg-panel rounded-3xl p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-ink-50">Latest summary</h3>
          <span className="text-xs text-ink-400">Last upload · Today</span>
        </div>
        {state.status !== 'success' && (
          <div className="mt-4 space-y-4 text-sm text-ink-400">
            <p>Upload a gradebook to see risk distribution and top students in this panel.</p>
            <div className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4">
              <p className="text-xs uppercase tracking-[0.3em] text-ink-500">Recent uploads</p>
              <ul className="mt-3 space-y-2 text-xs text-ink-400">
                <li>Fall 2025 baseline · Pending</li>
                <li>Attendance refresh · Pending</li>
              </ul>
            </div>
          </div>
        )}
        {state.status === 'success' && state.result && (
          <div className="mt-6 space-y-4">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="rounded-2xl bg-rose-900/40 p-3">
                <p className="text-xs uppercase tracking-[0.25em] text-rose-200">High</p>
                <p className="mt-1 text-xl font-semibold text-rose-100">
                  {state.result.summary.high}
                </p>
              </div>
              <div className="rounded-2xl bg-amber-900/40 p-3">
                <p className="text-xs uppercase tracking-[0.25em] text-amber-200">Moderate</p>
                <p className="mt-1 text-xl font-semibold text-amber-100">
                  {state.result.summary.medium}
                </p>
              </div>
              <div className="rounded-2xl bg-sage-900/40 p-3">
                <p className="text-xs uppercase tracking-[0.25em] text-sage-200">Low</p>
                <p className="mt-1 text-xl font-semibold text-sage-100">
                  {state.result.summary.low}
                </p>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-ink-200">Top predictions</h4>
              <div className="mt-3 max-h-64 space-y-3 overflow-auto pr-2">
                {state.result.predictions.slice(0, 8).map((prediction) => (
                  <div
                    key={`${prediction.student_id}-${prediction.risk_probability}`}
                    className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3"
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-ink-100">
                        {prediction.name ?? `Student ${prediction.student_id}`}
                      </p>
                      <span
                        className={clsx('badge', {
                          'badge-risk-high': prediction.risk_level === 'danger',
                          'badge-risk-medium': prediction.risk_level === 'warning',
                          'badge-risk-low': prediction.risk_level === 'success'
                        })}
                      >
                        {prediction.risk_category ?? 'Unknown'}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-ink-400">
                      GPA {prediction.current_gpa ?? '-'} · Attendance{' '}
                      {prediction.attendance_rate ?
                        `${Math.round(Number(prediction.attendance_rate) * 100)}%` :
                        '-'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-ink-700/60 bg-ink-950/50 p-4 text-xs text-ink-400">
              Previewed {Math.min(state.result.predictions.length, 8)} of{' '}
              {state.result.predictions.length} predictions.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
