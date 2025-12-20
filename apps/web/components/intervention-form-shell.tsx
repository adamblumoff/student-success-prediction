'use client';

import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import InterventionForm from '@/components/intervention-form';

const STORAGE_PREFIX = 'insight-prefill:';

type PrefillPayload = {
  studentId?: number;
  studentName?: string | null;
  title?: string;
  description?: string;
  interventionType?: string;
};

export default function InterventionFormShell({
  students
}: {
  students: Array<{ id: number; name: string | null; studentId: string }>;
}) {
  const searchParams = useSearchParams();
  const token = searchParams.get('prefill');
  const [prefill, setPrefill] = useState<PrefillPayload | null>(null);

  useEffect(() => {
    if (!token) {
      setPrefill(null);
      return;
    }
    const stored = sessionStorage.getItem(`${STORAGE_PREFIX}${token}`);
    if (!stored) {
      setPrefill(null);
      return;
    }
    try {
      const payload = JSON.parse(stored) as PrefillPayload;
      setPrefill(payload);
    } catch {
      setPrefill(null);
    }
  }, [token]);

  const defaults = useMemo(() => {
    if (!prefill) return undefined;
    const studentId = prefill.studentId;
    return {
      studentId,
      title: prefill.title ?? 'Insight plan',
      description: prefill.description ?? '',
      interventionType: prefill.interventionType ?? 'Insight plan'
    };
  }, [prefill]);

  return (
    <InterventionForm
      students={students}
      defaults={defaults}
      prefillToken={token}
      prefillStudentName={prefill?.studentName ?? null}
    />
  );
}
