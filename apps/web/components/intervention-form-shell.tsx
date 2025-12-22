'use client';

import { useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import InterventionForm from '@/components/intervention-form';

const STORAGE_PREFIX = 'insight-prefill:';

type PrefillPayload = {
  studentId?: number;
  studentName?: string | null;
  title?: string;
  description?: string;
  interventionType?: string;
  source?: 'insight' | 'student';
};

export default function InterventionFormShell({
  students
}: {
  students: Array<{ id: number; name: string | null; studentId: string }>;
}) {
  const searchParams = useSearchParams();
  const token = searchParams.get('prefill');
  const prefill = useMemo<PrefillPayload | null>(() => {
    if (!token || typeof window === 'undefined') return null;
    const stored = sessionStorage.getItem(`${STORAGE_PREFIX}${token}`);
    if (!stored) return null;
    try {
      return JSON.parse(stored) as PrefillPayload;
    } catch {
      return null;
    }
  }, [token]);

  const defaults = useMemo(() => {
    if (!prefill) return undefined;
    const studentId = prefill.studentId;
    return {
      studentId,
      title: prefill.title ?? '',
      description: prefill.description ?? '',
      interventionType: prefill.interventionType ?? ''
    };
  }, [prefill]);

  return (
    <InterventionForm
      key={token ?? 'empty'}
      students={students}
      defaults={defaults}
      prefillStudentName={prefill?.studentName ?? null}
      prefillSource={prefill?.source ?? null}
    />
  );
}
