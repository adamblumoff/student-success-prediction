import Link from 'next/link';
import { loadExistingStudents } from '@/lib/data/students';

export default async function StudentsPage() {
  const students = await loadExistingStudents();

  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-ink-400">Students</p>
        <h1 className="mt-2 text-3xl font-semibold">Student roster</h1>
        <p className="mt-2 text-sm text-ink-600">
          Browse students pulled from the production database and jump into insights.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {students.map((student) => (
          <div key={student.id} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-lg font-semibold text-ink-900">
                  {student.name ?? `Student ${student.studentId}`}
                </p>
                <p className="text-sm text-ink-500">
                  Grade {student.gradeLevel ?? '-'} - GPA {student.currentGpa ?? '-'}
                </p>
              </div>
              <Link
                href={`/insights?student=${student.id}`}
                className="rounded-full border border-ink-200 px-4 py-2 text-xs font-semibold"
              >
                View insights
              </Link>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-ink-500">
              <div>
                Attendance:{' '}
                {student.attendanceRate ? `${Math.round(student.attendanceRate * 100)}%` : '-'}
              </div>
              <div>Enrollment: {student.enrollmentStatus ?? 'active'}</div>
            </div>
          </div>
        ))}
      </div>
      {students.length === 0 && (
        <div className="bg-panel rounded-3xl p-8 text-sm text-ink-600">
          No students yet. Upload a gradebook to populate the roster.
        </div>
      )}
    </section>
  );
}
