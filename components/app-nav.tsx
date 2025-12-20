import Link from 'next/link';
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
  return (
    <nav className="flex flex-wrap items-center justify-between gap-6 rounded-3xl border border-ink-100 bg-white/90 px-6 py-4 shadow-[0_20px_50px_-40px_rgba(25,24,22,0.45)]">
      <div className="flex items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-2xl bg-ink-900 text-ink-50 font-semibold">
          SS
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-ink-400">Studio</p>
          <p className="text-lg font-semibold text-ink-800">Student Success</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="flex items-center gap-2 rounded-full border border-transparent px-4 py-2 text-sm font-medium text-ink-700 transition hover:border-ink-200 hover:bg-ink-50"
          >
            <link.icon className="h-4 w-4" />
            {link.label}
          </Link>
        ))}
      </div>
      <UserButton afterSignOutUrl="/" />
    </nav>
  );
}
