import Link from 'next/link';
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/nextjs';

export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-12">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-sage-600 text-white grid place-items-center font-semibold">
              SS
            </div>
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-ink-400">Student Success</p>
              <p className="text-xl font-semibold">Early Warning + Intervention Studio</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="rounded-full border border-ink-300 px-5 py-2 text-sm font-semibold">
                  Sign in
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <UserButton afterSignOutUrl="/" />
              <Link
                href="/dashboard"
                className="rounded-full bg-ink-900 px-5 py-2 text-sm font-semibold text-ink-50"
              >
                Open dashboard
              </Link>
            </SignedIn>
          </div>
        </header>

        <section className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="card">
            <p className="badge badge-risk-low">AI-augmented workflow</p>
            <h1 className="mt-5 text-4xl font-semibold leading-tight text-ink-900 md:text-5xl">
              Reimagine the way districts respond to risk - faster, calmer, and deeply
              contextual.
            </h1>
            <p className="mt-6 text-lg text-ink-600">
              Upload gradebook data, surface high-risk learners, and orchestrate
              interventions with real-time updates, GPT insights, and shared
              accountability across teams.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="rounded-full bg-sage-600 px-6 py-3 text-sm font-semibold text-white">
                    Get started
                  </button>
                </SignInButton>
              </SignedOut>
              <SignedIn>
                <Link
                  href="/upload"
                  className="rounded-full bg-sage-600 px-6 py-3 text-sm font-semibold text-white"
                >
                  Upload gradebook
                </Link>
              </SignedIn>
              <Link
                href="/dashboard"
                className="rounded-full border border-ink-300 px-6 py-3 text-sm font-semibold"
              >
                View insights
              </Link>
            </div>
          </div>
          <div className="bg-panel rounded-3xl p-6">
            <div className="flex flex-col gap-6">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-ink-400">Live workflow</p>
                <h2 className="mt-2 text-2xl font-semibold">What the new app does</h2>
              </div>
              <ul className="space-y-4 text-sm text-ink-700">
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
              <div className="rounded-2xl border border-ink-100 bg-white/70 p-4 text-xs text-ink-500">
                Deployed on Railway - PostgreSQL single source of truth - Clerk auth
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
