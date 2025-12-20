import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import AppNav from '@/components/app-nav';
import { ensureAppUser } from '@/lib/auth';

export default async function AppLayout({
  children
}: {
  children: React.ReactNode;
}) {
  const { userId } = await auth();
  if (!userId) {
    redirect('/sign-in');
  }

  await ensureAppUser();

  return (
    <main className="min-h-screen px-6 py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">
        <AppNav />
        {children}
      </div>
    </main>
  );
}
