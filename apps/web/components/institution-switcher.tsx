'use client';

import SubmitButton from '@/components/submit-button';
import { useState } from 'react';
import { useAppData } from '@/components/app-data-provider';

type InstitutionOption = {
  id: number;
  name: string;
};

type InstitutionSwitcherProps = {
  institutions: InstitutionOption[];
};

export default function InstitutionSwitcher({
  institutions
}: InstitutionSwitcherProps) {
  const { selectedInstitutionId, setSelectedInstitutionId } = useAppData();
  const [draftId, setDraftId] = useState<number | null>(null);
  const value = draftId ?? selectedInstitutionId ?? institutions[0]?.id ?? null;

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (!value) return;
        setSelectedInstitutionId(value);
        setDraftId(null);
      }}
      className="flex items-center gap-2"
    >
      <label className="text-xs uppercase tracking-[0.3em] text-ink-500">School</label>
      <select
        name="institutionId"
        value={value ?? ''}
        onChange={(event) => setDraftId(Number(event.target.value))}
        className="rounded-full border border-ink-700/60 bg-ink-950/60 px-3 py-2 text-xs text-ink-100"
      >
        {institutions.map((item) => (
          <option key={item.id} value={item.id}>
            {item.name}
          </option>
        ))}
      </select>
      <SubmitButton
        label="Apply"
        pendingLabel="Applying..."
        className="rounded-full border border-ink-700/60 px-3 py-2 text-xs font-semibold uppercase tracking-[0.25em] text-ink-200"
        disabled={value === selectedInstitutionId}
      />
    </form>
  );
}
