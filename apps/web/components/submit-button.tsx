'use client';

import { useFormStatus } from 'react-dom';

type SubmitButtonProps = {
  label: string;
  pendingLabel?: string;
  className?: string;
  disabled?: boolean;
};

export default function SubmitButton({
  label,
  pendingLabel = 'Saving...',
  className,
  disabled
}: SubmitButtonProps) {
  const { pending } = useFormStatus();
  const isDisabled = pending || Boolean(disabled);

  return (
    <button type="submit" className={className} disabled={isDisabled} aria-disabled={isDisabled}>
      {pending ? pendingLabel : label}
    </button>
  );
}
