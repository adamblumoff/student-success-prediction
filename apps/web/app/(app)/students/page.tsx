import { loadStudentsWithRisk } from '@/lib/data/students';
import StudentRoster from '@/components/student-roster';

export default async function StudentsPage() {
  const students = await loadStudentsWithRisk();

  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-ink-400">Students</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink-50">Student roster</h1>
        <p className="mt-2 text-sm text-ink-300">
          Browse students pulled from the production database and jump into insights.
        </p>
      </div>
      <StudentRoster students={students} />
      {students.length === 0 && (
        <div className="bg-panel rounded-3xl p-8 text-sm text-ink-300">
          No students yet. Upload a gradebook to populate the roster.
        </div>
      )}
    </section>
  );
}
