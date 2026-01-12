'use client';

import { useEffect, useMemo } from 'react';
import StudentRoster from '@/components/student-roster';
import { useAppData, type StudentWithRisk } from '@/components/app-data-provider';

export default function StudentsPageClient({
  initialStudents,
  initialInstitutionId
}: {
  initialStudents: StudentWithRisk[];
  initialInstitutionId: number | null;
}) {
  const {
    students: contextStudents,
    isLoadingAll,
    selectedInstitutionId,
    seedStudentsForInstitution,
    studentsVersionByInstitution
  } = useAppData();

  useEffect(() => {
    if (!selectedInstitutionId) return;
    if (initialInstitutionId !== selectedInstitutionId) return;
    if (initialStudents.length === 0) return;
    seedStudentsForInstitution(selectedInstitutionId, initialStudents);
  }, [
    initialInstitutionId,
    initialStudents,
    seedStudentsForInstitution,
    selectedInstitutionId
  ]);

  const students = useMemo(() => {
    if (selectedInstitutionId && selectedInstitutionId !== initialInstitutionId) {
      return contextStudents;
    }
    return contextStudents.length > 0 ? contextStudents : initialStudents;
  }, [contextStudents, initialInstitutionId, initialStudents, selectedInstitutionId]);

  const versionKey = selectedInstitutionId
    ? studentsVersionByInstitution[selectedInstitutionId]
    : undefined;

  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs uppercase text-ink-400">Students</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink-50 text-balance">Student roster</h1>
        <p className="mt-2 text-sm text-ink-300 text-pretty">
          Browse students pulled from the production database and jump into insights.
        </p>
      </div>
      <StudentRoster students={students} versionKey={versionKey} />
      {students.length === 0 && (
        <div className="bg-panel rounded-3xl p-8 text-sm text-ink-300 text-pretty">
          {isLoadingAll
            ? 'Loading school roster…'
            : 'No students yet. Upload a gradebook to populate the roster.'}
        </div>
      )}
    </section>
  );
}
