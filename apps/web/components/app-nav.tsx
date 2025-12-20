'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UserButton } from '@clerk/nextjs';
import { BarChart3, UploadCloud, Users, Sparkles, CalendarClock, Plug } from 'lucide-react';

const links = [
  { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { href: '/upload', label: 'Upload', icon: UploadCloud },
  { href: '/students', label: 'Students', icon: Users },
  { href: '/interventions', label: 'Interventions', icon: CalendarClock },
  { href: '/insights', label: 'GPT Insights', icon: Sparkles },
  { href: '/integrations', label: 'Integrations', icon: Plug }
];

export default function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-wrap items-center justify-between gap-6 rounded-3xl border border-ink-700/60 bg-ink-900/80 px-6 py-4 shadow-[0_30px_70px_-50px_rgba(8,10,16,0.9)]">
      <div className="flex items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-2xl bg-slate-950 text-ink-50 font-semibold">
          SS
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-ink-400">Studio</p>
          <p className="text-lg font-semibold text-ink-50">Student Success</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition ${
                active
                  ? 'border border-sage-400/50 bg-sage-500/10 text-ink-50'
                  : 'border border-transparent text-ink-300 hover:border-ink-600/60 hover:bg-ink-800/60 hover:text-ink-100'
              }`}
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
