'use client';

import { useEffect, useMemo } from 'react';
import StudentRoster from '@/components/student-roster';
import { useAppData, type StudentWithRisk } from '@/components/app-data-provider';

export default function StudentsPageClient({
  initialStudents
}: {
  initialStudents: StudentWithRisk[];
}) {
  const { students: contextStudents, isLoadingAll, selectedInstitutionId, seedStudentsForInstitution } =
    useAppData();

  useEffect(() => {
    if (!selectedInstitutionId) return;
    if (initialStudents.length === 0) return;
    seedStudentsForInstitution(selectedInstitutionId, initialStudents);
  }, [initialStudents, seedStudentsForInstitution, selectedInstitutionId]);

  const students = useMemo(
    () => (contextStudents.length > 0 ? contextStudents : initialStudents),
    [contextStudents, initialStudents]
  );

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
          {isLoadingAll ? 'Loading school roster…' : 'No students yet. Upload a gradebook to populate the roster.'}
        </div>
      )}
    </section>
  );
}
