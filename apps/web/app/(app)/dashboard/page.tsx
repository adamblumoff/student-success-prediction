import Link from 'next/link';
import { getDashboardStats } from '@/lib/data/dashboard';

export default async function DashboardPage() {
  const stats = await getDashboardStats();
  const predictionDelta =
    stats.previousPredictions === 0
      ? null
      : Math.round(
          ((stats.recentPredictions - stats.previousPredictions) / stats.previousPredictions) * 100
        );

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-ink-400">System snapshot</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink-50">District health overview</h1>
          <p className="mt-2 text-sm text-ink-300">
            The latest student risk landscape, refreshed from the production data pipeline.
          </p>
        </div>
        <div className="flex items-center gap-3 rounded-full border border-ink-700/60 bg-ink-900/80 p-1 text-xs font-semibold text-ink-300">
          {['7d', '30d', '90d', 'Term'].map((range, index) => (
            <button
              key={range}
              type="button"
              className={`rounded-full px-4 py-2 ${
                index === 1 ? 'bg-ink-700/70 text-ink-50' : 'hover:bg-ink-800/60'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="card">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <p className="badge badge-risk-low">District snapshot</p>
            <span className="text-xs text-ink-400">
              Data updated{' '}
              {stats.latestPredictionDate
                ? new Date(stats.latestPredictionDate).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric'
                  })
                : '—'}
            </span>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4">
              <p className="text-xs uppercase tracking-[0.3em] text-ink-500">Students</p>
              <p className="mt-2 text-2xl font-semibold text-ink-50">{stats.totalStudents}</p>
            </div>
            <div className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4">
              <p className="text-xs uppercase tracking-[0.3em] text-ink-500">Predictions</p>
              <p className="mt-2 text-2xl font-semibold text-ink-50">{stats.totalPredictions}</p>
            </div>
            <div className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4">
              <p className="text-xs uppercase tracking-[0.3em] text-ink-500">Interventions</p>
              <p className="mt-2 text-2xl font-semibold text-ink-50">
                {stats.totalInterventions}
              </p>
            </div>
          </div>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl bg-sage-900/40 p-4 text-sage-200">
              <p className="text-xs uppercase tracking-[0.3em]">Low risk</p>
              <p className="mt-2 text-xl font-semibold">{stats.riskDistribution.low}</p>
            </div>
            <div className="rounded-2xl bg-amber-900/40 p-4 text-amber-200">
              <p className="text-xs uppercase tracking-[0.3em]">Moderate risk</p>
              <p className="mt-2 text-xl font-semibold">{stats.riskDistribution.medium}</p>
            </div>
            <div className="rounded-2xl bg-rose-900/40 p-4 text-rose-200">
              <p className="text-xs uppercase tracking-[0.3em]">High risk</p>
              <p className="mt-2 text-xl font-semibold">{stats.riskDistribution.high}</p>
            </div>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-ink-700/50 bg-ink-950/50 p-4 text-sm">
              <p className="text-xs uppercase tracking-[0.3em] text-ink-500">
                New predictions
              </p>
              <p className="mt-2 text-lg font-semibold text-ink-50">
                {stats.recentPredictions}
              </p>
              <p className="mt-1 text-xs text-ink-400">
                {predictionDelta === null
                  ? 'No prior data'
                  : `${predictionDelta >= 0 ? '+' : ''}${predictionDelta}% vs last week`}
              </p>
            </div>
            <div className="rounded-2xl border border-ink-700/50 bg-ink-950/50 p-4 text-sm">
              <p className="text-xs uppercase tracking-[0.3em] text-ink-500">
                Interventions created
              </p>
              <p className="mt-2 text-lg font-semibold text-ink-50">
                {stats.recentInterventions}
              </p>
              <p className="mt-1 text-xs text-ink-400">Last 7 days</p>
            </div>
            <div className="rounded-2xl border border-ink-700/50 bg-ink-950/50 p-4 text-sm">
              <p className="text-xs uppercase tracking-[0.3em] text-ink-500">
                Interventions closed
              </p>
              <p className="mt-2 text-lg font-semibold text-ink-50">
                {stats.completedInterventions}
              </p>
              <p className="mt-1 text-xs text-ink-400">Last 7 days</p>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-panel rounded-3xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-ink-400">At risk</p>
                <h2 className="mt-2 text-xl font-semibold text-ink-50">
                  Top students to review
                </h2>
              </div>
              <Link
                href="/students"
                className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-200"
              >
                View roster
              </Link>
            </div>
            <div className="mt-5 space-y-3">
              {stats.topRiskStudents.map((student) => (
                <div
                  key={student.id}
                  className="flex items-center justify-between rounded-2xl border border-ink-700/60 bg-ink-950/50 px-4 py-3 text-sm"
                >
                  <div>
                    <p className="font-semibold text-ink-50">
                      {student.name ?? `Student ${student.studentId ?? student.id}`}
                    </p>
                    <p className="text-xs text-ink-400">
                      Grade {student.gradeLevel ?? '-'} · Risk score{' '}
                      {student.riskScore.toFixed(2)}
                    </p>
                  </div>
                  <span
                    className={`badge ${
                      student.riskCategory?.toLowerCase().includes('high')
                        ? 'badge-risk-high'
                        : student.riskCategory?.toLowerCase().includes('moderate') ||
                            student.riskCategory?.toLowerCase().includes('medium')
                          ? 'badge-risk-medium'
                          : 'badge-risk-low'
                    }`}
                  >
                    {student.riskCategory ?? 'Risk'}
                  </span>
                </div>
              ))}
              {stats.topRiskStudents.length === 0 && (
                <p className="text-sm text-ink-400">No predictions yet.</p>
              )}
            </div>
          </div>

          <div className="bg-panel rounded-3xl p-6">
            <h2 className="text-xl font-semibold text-ink-50">Quick actions</h2>
            <p className="mt-3 text-sm text-ink-300">
              Jump directly into the workflows that unblock your team.
            </p>
            <div className="mt-6 flex flex-col gap-3">
              <Link
                href="/upload"
                className="rounded-2xl border border-ink-700/60 bg-ink-950/60 px-4 py-3 text-sm font-semibold text-ink-100"
              >
                Upload a new gradebook
              </Link>
              <Link
                href="/students"
                className="rounded-2xl border border-ink-700/60 bg-ink-950/60 px-4 py-3 text-sm font-semibold text-ink-100"
              >
                Review student roster
              </Link>
              <Link
                href="/interventions"
                className="rounded-2xl border border-ink-700/60 bg-ink-950/60 px-4 py-3 text-sm font-semibold text-ink-100"
              >
                Plan interventions
              </Link>
            </div>
          </div>
        </div>
      </section>
    </section>
  );
}
