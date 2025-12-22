import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import AppNav from '@/components/app-nav';
import { ensureAppUser } from '@/lib/auth';
import { loadTenantSummary } from '@/lib/data/tenant';
import InstitutionSwitcher from '@/components/institution-switcher';
import AppDataProvider from '@/components/app-data-provider';
import { loadStudentsWithRisk } from '@/lib/data/students';
import { loadLatestInsights } from '@/lib/data/insights';
import { listInterventions } from '@/lib/data/interventions';

const toIso = (value: Date | string | null) => {
  if (!value) return null;
  if (value instanceof Date) return value.toISOString();
  return value;
};

export const revalidate = 0;

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
  const { district, institution, institutions } = await loadTenantSummary();
  const fallbackInstitutionId = institution?.id ?? institutions[0]?.id ?? 0;
  const [students, interventions] = await Promise.all([
    loadStudentsWithRisk(),
    listInterventions()
  ]);
  const latestInsights = await loadLatestInsights(students.map((student) => student.id));

  return (
    <AppDataProvider
      institutions={institutions}
      initialInstitutionId={institution?.id ?? null}
      initialStudents={students.map((student) => ({
        ...student,
        institutionId: student.institutionId,
        lastActivity: toIso(student.lastActivity),
        predictionDate: toIso(student.predictionDate)
      }))}
      initialInsights={latestInsights.map((insight) => ({
        studentDatabaseId: insight.studentDatabaseId ?? 0,
        institutionId: fallbackInstitutionId,
        formattedHtml: insight.formattedHtml ?? null,
        riskLevel: insight.riskLevel ?? null,
        createdAt: toIso(insight.createdAt)
      }))}
      initialInterventions={interventions.map((row) => ({
        id: row.intervention.id,
        studentId: row.intervention.studentId ?? null,
        institutionId: row.intervention.institutionId,
        title: row.intervention.title,
        interventionType: row.intervention.interventionType,
        status: row.intervention.status,
        priority: row.intervention.priority,
        assignedTo: row.intervention.assignedTo,
        dueDate: toIso(row.intervention.dueDate),
        createdAt: toIso(row.intervention.createdAt),
        completedDate: toIso(row.intervention.completedDate),
        studentName: row.student?.name ?? null,
        studentIdentifier: row.student?.studentId ?? null
      }))}
    >
      <main className="min-h-screen px-6 py-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-6">
          <AppNav />
          <div className="flex flex-wrap items-center gap-4 rounded-3xl border border-ink-700/50 bg-ink-900/70 px-6 py-4 text-sm text-ink-200">
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase tracking-[0.3em] text-ink-500">District</span>
              <span className="font-semibold text-ink-50">{district?.name ?? 'District'}</span>
            </div>
            <div className="h-4 w-px bg-ink-700/70" />
            <InstitutionSwitcher institutions={institutions} />
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
    </AppDataProvider>
  );
}
