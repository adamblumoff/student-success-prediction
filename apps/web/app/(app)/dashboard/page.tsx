import Link from 'next/link';
import { getDashboardStats } from '@/lib/data/dashboard';

export default async function DashboardPage() {
  const stats = await getDashboardStats();

  return (
    <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
      <div className="card">
        <p className="badge badge-risk-low">System snapshot</p>
        <h1 className="mt-4 text-3xl font-semibold">District health overview</h1>
        <p className="mt-3 text-ink-600">
          The latest student risk landscape, pulled directly from the production data
          pipeline.
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-ink-100 bg-ink-50 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-ink-400">Students</p>
            <p className="mt-2 text-2xl font-semibold text-ink-900">{stats.totalStudents}</p>
          </div>
          <div className="rounded-2xl border border-ink-100 bg-ink-50 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-ink-400">Predictions</p>
            <p className="mt-2 text-2xl font-semibold text-ink-900">{stats.totalPredictions}</p>
          </div>
          <div className="rounded-2xl border border-ink-100 bg-ink-50 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-ink-400">Interventions</p>
            <p className="mt-2 text-2xl font-semibold text-ink-900">{stats.totalInterventions}</p>
          </div>
        </div>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl bg-sage-50 p-4 text-sage-700">
            <p className="text-xs uppercase tracking-[0.3em]">Low risk</p>
            <p className="mt-2 text-xl font-semibold">{stats.riskDistribution.low}</p>
          </div>
          <div className="rounded-2xl bg-amber-50 p-4 text-amber-700">
            <p className="text-xs uppercase tracking-[0.3em]">Moderate risk</p>
            <p className="mt-2 text-xl font-semibold">{stats.riskDistribution.medium}</p>
          </div>
          <div className="rounded-2xl bg-rose-50 p-4 text-rose-700">
            <p className="text-xs uppercase tracking-[0.3em]">High risk</p>
            <p className="mt-2 text-xl font-semibold">{stats.riskDistribution.high}</p>
          </div>
        </div>
      </div>
      <div className="bg-panel rounded-3xl p-6">
        <h2 className="text-xl font-semibold">Next actions</h2>
        <p className="mt-3 text-sm text-ink-600">
          Move directly into analysis or interventions without leaving the live data
          pipeline.
        </p>
        <div className="mt-6 flex flex-col gap-3">
          <Link
            href="/upload"
            className="rounded-2xl border border-ink-100 bg-white px-4 py-3 text-sm font-semibold"
          >
            Upload a new gradebook
          </Link>
          <Link
            href="/students"
            className="rounded-2xl border border-ink-100 bg-white px-4 py-3 text-sm font-semibold"
          >
            Review student roster
          </Link>
          <Link
            href="/interventions"
            className="rounded-2xl border border-ink-100 bg-white px-4 py-3 text-sm font-semibold"
          >
            Plan interventions
          </Link>
        </div>
      </div>
    </section>
  );
}
