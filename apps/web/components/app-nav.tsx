'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UserButton } from '@clerk/nextjs';
import { BarChart3, UploadCloud, Users, Sparkles, CalendarClock, Plug, Settings } from 'lucide-react';
import { cn } from '@/lib/cn';

const links = [
  { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { href: '/upload', label: 'Upload', icon: UploadCloud },
  { href: '/students', label: 'Students', icon: Users },
  { href: '/interventions', label: 'Interventions', icon: CalendarClock },
  { href: '/insights', label: 'GPT Insights', icon: Sparkles },
  { href: '/integrations', label: 'Integrations', icon: Plug },
  { href: '/settings', label: 'Settings', icon: Settings }
];

export default function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-wrap items-center justify-between gap-6 rounded-3xl border border-ink-700/60 bg-ink-900/80 px-6 py-4 shadow-2xl">
      <Link href="/dashboard" className="flex items-center gap-3">
        <div className="grid size-10 place-items-center rounded-2xl bg-slate-950 text-[0.65rem] font-semibold leading-none text-ink-50">
          SSP
        </div>
        <div>
          <p className="text-xs uppercase text-ink-400">Studio</p>
          <p className="text-lg font-semibold text-ink-50 text-balance">Student Success</p>
        </div>
      </Link>
      <div className="flex flex-wrap items-center gap-2">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                'flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition',
                active
                  ? 'border border-sage-400/50 bg-sage-500/10 text-ink-50'
                  : 'border border-transparent text-ink-300 hover:border-ink-600/60 hover:bg-ink-800/60 hover:text-ink-100'
              )}
            >
              <link.icon className="h-4 w-4" />
              {link.label}
            </Link>
          );
        })}
      </div>
      <UserButton afterSignOutUrl="/" />
    </nav>
  );
}
