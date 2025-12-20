import Link from 'next/link';
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/nextjs';

export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-12">
        <header className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-2xl bg-sage-500 text-[0.65rem] font-semibold leading-none text-white">
              SSP
            </div>
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-ink-400">Student Success</p>
              <p className="text-xl font-semibold text-ink-50">
                Early Warning + Intervention Studio
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="rounded-full border border-ink-600/60 px-5 py-2 text-sm font-semibold text-ink-100">
                  Sign in
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <UserButton afterSignOutUrl="/" />
              <Link
                href="/dashboard"
                className="rounded-full bg-sage-500 px-5 py-2 text-sm font-semibold text-slate-950"
              >
                Open dashboard
              </Link>
            </SignedIn>
          </div>
        </header>

        <section className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="card">
            <p className="badge badge-risk-low">AI-augmented workflow</p>
            <h1 className="mt-5 text-4xl font-semibold leading-tight text-ink-50 md:text-5xl">
              Reimagine the way districts respond to risk - faster, calmer, and deeply
              contextual.
            </h1>
            <p className="mt-6 text-lg text-ink-200">
              Upload gradebook data, surface high-risk learners, and orchestrate
              interventions with real-time updates, GPT insights, and shared
              accountability across teams.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="rounded-full bg-sage-500 px-6 py-3 text-sm font-semibold text-slate-950">
                    Get started
                  </button>
                </SignInButton>
              </SignedOut>
              <SignedIn>
                <Link
                  href="/upload"
                  className="rounded-full bg-sage-500 px-6 py-3 text-sm font-semibold text-slate-950"
                >
                  Upload gradebook
                </Link>
              </SignedIn>
              <Link
                href="/dashboard"
                className="rounded-full border border-ink-600/70 px-6 py-3 text-sm font-semibold text-ink-100"
              >
                View insights
              </Link>
            </div>
            <div className="mt-10 grid gap-4 md:grid-cols-3">
              {[
                {
                  title: '1. Upload & map',
                  description: 'Drop in CSVs or connect SIS data, then validate columns.'
                },
                {
                  title: '2. Review risk',
                  description: 'See district, school, and student risk with confidence bands.'
                },
                {
                  title: '3. Intervene',
                  description: 'Assign plans, track ownership, and close the loop.'
                }
              ].map((step) => (
                <div
                  key={step.title}
                  className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4 text-sm text-ink-200"
                >
                  <p className="text-xs uppercase tracking-[0.24em] text-ink-500">
                    {step.title}
                  </p>
                  <p className="mt-2 text-sm text-ink-200">{step.description}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-panel rounded-3xl p-6">
            <div className="flex flex-col gap-6">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-ink-400">Live workflow</p>
                <h2 className="mt-2 text-2xl font-semibold text-ink-50">
                  What the new app does
                </h2>
              </div>
              <ul className="space-y-4 text-sm text-ink-200">
                <li className="flex items-start gap-3">
                  <span className="mt-1 h-2 w-2 rounded-full bg-sage-600" />
                  ML-driven risk predictions with transparent confidence scoring.
                </li>
                <li className="flex items-start gap-3">
                  <span className="mt-1 h-2 w-2 rounded-full bg-amber-500" />
                  Intervention planning with ownership, due dates, and outcomes.
                </li>
                <li className="flex items-start gap-3">
                  <span className="mt-1 h-2 w-2 rounded-full bg-rose-500" />
                  GPT insights that adapt to your current student data.
                </li>
                <li className="flex items-start gap-3">
                  <span className="mt-1 h-2 w-2 rounded-full bg-ink-500" />
                  Shared collaboration workflows and visibility across teams.
                </li>
              </ul>
              <div className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4 text-xs text-ink-400">
                Deployed on Railway - PostgreSQL single source of truth - Clerk auth
              </div>
              <div className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-ink-500">
                  Snapshot preview
                </p>
                <div className="mt-3 grid gap-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-ink-200">High-risk students</span>
                    <span className="font-semibold text-rose-300">18</span>
                  </div>
                  <div className="h-2 rounded-full bg-ink-800">
                    <div className="h-2 w-2/3 rounded-full bg-rose-500" />
                  </div>
                  <div className="grid gap-2 text-xs text-ink-300">
                    <div className="flex items-center justify-between rounded-xl border border-ink-700/50 bg-ink-900/70 px-3 py-2">
                      <span>Maria Johnson · Grade 9</span>
                      <span className="badge badge-risk-high">High</span>
                    </div>
                    <div className="flex items-center justify-between rounded-xl border border-ink-700/50 bg-ink-900/70 px-3 py-2">
                      <span>James Thomas · Grade 10</span>
                      <span className="badge badge-risk-medium">Moderate</span>
                    </div>
                    <div className="flex items-center justify-between rounded-xl border border-ink-700/50 bg-ink-900/70 px-3 py-2">
                      <span>Emily Harris · Grade 11</span>
                      <span className="badge badge-risk-low">Low</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
