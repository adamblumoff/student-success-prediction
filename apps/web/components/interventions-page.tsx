'use client';

import { useEffect, useMemo } from 'react';
import InterventionFormShell from '@/components/intervention-form-shell';
import InterventionTable from '@/components/intervention-table';
import { useAppData } from '@/components/app-data-provider';

export default function InterventionsPageClient({
  initialStudents,
  initialInterventions,
  initialInstitutionId
}: {
  initialStudents: {
    id: number;
    institutionId: number;
    studentId: string;
    name: string | null;
    gradeLevel: string | null;
    currentGpa: number | null;
    attendanceRate: number | null;
    enrollmentStatus: string | null;
    assignedCounselor: string | null;
    lastActivity: string | null;
    activeInterventions: number | null;
    riskCategory: string | null;
    riskScore: number | null;
    confidenceScore: number | null;
    predictionDate: string | null;
  }[];
  initialInterventions: {
    id: number;
    studentId: number | null;
    institutionId: number;
    title: string;
    interventionType: string;
    status: string | null;
    priority: string | null;
    assignedTo: string | null;
    dueDate: string | null;
    createdAt: string | null;
    completedDate: string | null;
    studentName: string | null;
    studentIdentifier: string | null;
  }[];
  initialInstitutionId: number | null;
}) {
  const {
    students,
    interventions,
    selectedInstitutionId,
    seedStudentsForInstitution,
    seedInterventionsForInstitution,
    loadInterventionsForInstitution,
    isLoadingInterventions
  } = useAppData();

  useEffect(() => {
    if (!selectedInstitutionId) return;
    if (initialInstitutionId !== selectedInstitutionId) return;
    if (initialStudents.length > 0) {
      seedStudentsForInstitution(selectedInstitutionId, initialStudents);
    }
  }, [
    initialInstitutionId,
    initialStudents,
    seedStudentsForInstitution,
    selectedInstitutionId
  ]);

  useEffect(() => {
    if (!selectedInstitutionId) return;
    if (initialInstitutionId !== selectedInstitutionId) return;
    if (initialInterventions.length > 0) {
      seedInterventionsForInstitution(selectedInstitutionId, initialInterventions);
    }
  }, [
    initialInstitutionId,
    initialInterventions,
    seedInterventionsForInstitution,
    selectedInstitutionId
  ]);

  useEffect(() => {
    if (!selectedInstitutionId) return;
    void loadInterventionsForInstitution(selectedInstitutionId);
  }, [loadInterventionsForInstitution, selectedInstitutionId]);

  const studentOptions = useMemo(() => {
    const source =
      selectedInstitutionId && selectedInstitutionId !== initialInstitutionId
        ? students
        : students.length > 0
          ? students
          : initialStudents;
    return source.map((student) => ({
      id: student.id,
      name: student.name,
      studentId: student.studentId
    }));
  }, [initialInstitutionId, initialStudents, selectedInstitutionId, students]);

  const rows = useMemo(() => {
    const source =
      selectedInstitutionId && selectedInstitutionId !== initialInstitutionId
        ? interventions
        : interventions.length > 0
          ? interventions
          : initialInterventions;
    return source.map((row) => ({
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
    }));
  }, [initialInstitutionId, initialInterventions, interventions, selectedInstitutionId]);

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
