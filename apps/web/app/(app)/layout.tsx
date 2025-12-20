import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import AppNav from '@/components/app-nav';
import { ensureAppUser } from '@/lib/auth';

export default async function AppLayout({
  children
}: {
  children: React.ReactNode;
}) {
  const updatedAt = new Date();

  const { userId } = await auth();
  if (!userId) {
    redirect('/sign-in');
  }

  await ensureAppUser();

  return (
    <main className="min-h-screen px-6 py-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <AppNav />
        <div className="flex flex-wrap items-center gap-4 rounded-3xl border border-ink-700/50 bg-ink-900/70 px-6 py-4 text-sm text-ink-200">
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase tracking-[0.3em] text-ink-500">District</span>
            <span className="font-semibold text-ink-50">Northwind School District</span>
          </div>
          <div className="h-4 w-px bg-ink-700/70" />
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase tracking-[0.3em] text-ink-500">Term</span>
            <span>Fall 2025</span>
          </div>
          <div className="h-4 w-px bg-ink-700/70" />
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase tracking-[0.3em] text-ink-500">Data Updated</span>
            <span>{updatedAt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
          </div>
        </div>
        {children}
      </div>
    </main>
  );
}
