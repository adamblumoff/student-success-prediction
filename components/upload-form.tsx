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
        'rounded-full px-6 py-3 text-sm font-semibold text-white',
        pending ? 'bg-ink-400' : 'bg-ink-900 hover:bg-ink-800'
      )}
      disabled={pending}
    >
      {pending ? 'Analyzing...' : 'Run analysis'}
    </button>
  );
}

export default function UploadForm() {
  const [state, formAction] = useActionState(analyzeGradebookAction, initialState);

  return (
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <form action={formAction} className="card flex flex-col gap-6">
        <div>
          <p className="badge badge-risk-low">Gradebook analysis</p>
          <h2 className="mt-4 text-2xl font-semibold">Upload your latest CSV</h2>
          <p className="mt-2 text-sm text-ink-600">
            We'll send the gradebook to the ML service and hydrate your dashboard with
            fresh predictions.
          </p>
        </div>
        <label className="flex flex-col gap-2 text-sm font-medium text-ink-700">
          Gradebook CSV
          <input
            type="file"
            name="file"
            accept=".csv"
            className="rounded-2xl border border-ink-200 bg-white p-3 text-sm"
            required
          />
        </label>
        <div className="flex items-center gap-4">
          <SubmitButton />
          {state.status === 'error' && (
            <span className="text-sm text-rose-600">{state.error}</span>
          )}
          {state.status === 'success' && (
            <span className="text-sm text-sage-700">Analysis complete.</span>
          )}
        </div>
      </form>

      <div className="bg-panel rounded-3xl p-6">
        <h3 className="text-lg font-semibold">Latest summary</h3>
        {state.status !== 'success' && (
          <p className="mt-3 text-sm text-ink-500">
            Upload a gradebook to see risk distribution and top students in this panel.
          </p>
        )}
        {state.status === 'success' && state.result && (
          <div className="mt-6 space-y-4">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="rounded-2xl bg-rose-50 p-3">
                <p className="text-xs uppercase tracking-[0.25em] text-rose-600">High</p>
                <p className="mt-1 text-xl font-semibold text-rose-700">
                  {state.result.summary.high}
                </p>
              </div>
              <div className="rounded-2xl bg-amber-50 p-3">
                <p className="text-xs uppercase tracking-[0.25em] text-amber-600">Moderate</p>
                <p className="mt-1 text-xl font-semibold text-amber-700">
                  {state.result.summary.medium}
                </p>
              </div>
              <div className="rounded-2xl bg-sage-50 p-3">
                <p className="text-xs uppercase tracking-[0.25em] text-sage-600">Low</p>
                <p className="mt-1 text-xl font-semibold text-sage-700">
                  {state.result.summary.low}
                </p>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-ink-700">Top predictions</h4>
              <div className="mt-3 max-h-64 space-y-3 overflow-auto pr-2">
                {state.result.predictions.slice(0, 8).map((prediction) => (
                  <div
                    key={`${prediction.student_id}-${prediction.risk_probability}`}
                    className="rounded-2xl border border-ink-100 bg-white p-3"
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-ink-800">
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
                    <p className="mt-2 text-xs text-ink-500">
                      GPA {prediction.current_gpa ?? '-'} - Attendance{' '}
                      {prediction.attendance_rate ?
                        `${Math.round(Number(prediction.attendance_rate) * 100)}%` :
                        '-'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
