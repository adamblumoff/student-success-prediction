'use client';

import { useEffect, useMemo } from 'react';
import InterventionFormShell from '@/components/intervention-form-shell';
import InterventionTable from '@/components/intervention-table';
import { useAppData } from '@/components/app-data-provider';

export default function InterventionsPageClient() {
  const {
    students,
    interventions,
    selectedInstitutionId,
    loadInterventionsForInstitution,
    isLoadingInterventions
  } = useAppData();

  useEffect(() => {
    if (!selectedInstitutionId) return;
    void loadInterventionsForInstitution(selectedInstitutionId);
  }, [loadInterventionsForInstitution, selectedInstitutionId]);

  const studentOptions = useMemo(
    () =>
      students.map((student) => ({
        id: student.id,
        name: student.name,
        studentId: student.studentId
      })),
    [students]
  );

  const rows = useMemo(
    () =>
      interventions.map((row) => ({
        intervention: {
          id: row.id,
          title: row.title,
          interventionType: row.interventionType,
          status: row.status,
          priority: row.priority,
          assignedTo: row.assignedTo,
          dueDate: row.dueDate
        },
        student: row.studentId
          ? { name: row.studentName, studentId: row.studentIdentifier ?? '' }
          : null
      })),
    [interventions]
  );

  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-ink-400">Interventions</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink-50">Plan support</h1>
        <p className="mt-2 text-sm text-ink-300">
          Create interventions with clear ownership, due dates, and outcomes for every
          student.
        </p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <InterventionFormShell students={studentOptions} />
        <InterventionTable initialRows={rows} />
      </div>
      {isLoadingInterventions && (
        <p className="text-xs uppercase tracking-[0.35em] text-ink-400">
          Loading interventions…
        </p>
      )}
    </section>
  );
}
