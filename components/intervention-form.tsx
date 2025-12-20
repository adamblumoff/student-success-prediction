'use client';

import { useFormState, useFormStatus } from 'react-dom';
import { createInterventionAction, type InterventionActionState } from '@/lib/actions/interventions';

const initialState: InterventionActionState = { status: 'idle' };

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      className="rounded-full bg-ink-900 px-5 py-2 text-sm font-semibold text-ink-50"
      disabled={pending}
    >
      {pending ? 'Saving...' : 'Create intervention'}
    </button>
  );
}

export default function InterventionForm({
  students
}: {
  students: Array<{ id: number; name: string | null; studentId: string }>;
}) {
  const [state, formAction] = useFormState(createInterventionAction, initialState);

  return (
    <form action={formAction} className="card space-y-4">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-ink-400">New intervention</p>
        <h2 className="mt-2 text-2xl font-semibold">Plan support</h2>
      </div>
      <label className="flex flex-col gap-2 text-sm">
        Student
        <select
          name="studentId"
          required
          className="rounded-2xl border border-ink-200 bg-white p-3 text-sm"
        >
          <option value="">Select student</option>
          {students.map((student) => (
            <option key={student.id} value={student.id}>
              {student.name ?? `Student ${student.studentId}`}
            </option>
          ))}
        </select>
      </label>
      <div className="grid gap-3 md:grid-cols-2">
        <label className="flex flex-col gap-2 text-sm">
          Title
          <input
            name="title"
            required
            className="rounded-2xl border border-ink-200 bg-white p-3 text-sm"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Type
          <input
            name="interventionType"
            required
            placeholder="tutoring, counseling, etc."
            className="rounded-2xl border border-ink-200 bg-white p-3 text-sm"
          />
        </label>
      </div>
      <label className="flex flex-col gap-2 text-sm">
        Description
        <textarea
          name="description"
          rows={3}
          className="rounded-2xl border border-ink-200 bg-white p-3 text-sm"
        />
      </label>
      <div className="grid gap-3 md:grid-cols-3">
        <label className="flex flex-col gap-2 text-sm">
          Priority
          <select
            name="priority"
            defaultValue="medium"
            className="rounded-2xl border border-ink-200 bg-white p-3 text-sm"
          >
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Status
          <select name="status" className="rounded-2xl border border-ink-200 bg-white p-3 text-sm">
            <option value="planned">Planned</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
          </select>
        </label>
        <label className="flex flex-col gap-2 text-sm">
          Due date
          <input type="date" name="dueDate" className="rounded-2xl border border-ink-200 bg-white p-3 text-sm" />
        </label>
      </div>
      <label className="flex flex-col gap-2 text-sm">
        Assigned to
        <input name="assignedTo" className="rounded-2xl border border-ink-200 bg-white p-3 text-sm" />
      </label>
      <div className="flex items-center gap-4">
        <SubmitButton />
        {state.status === 'error' && <p className="text-sm text-rose-600">{state.error}</p>}
        {state.status === 'success' && (
          <p className="text-sm text-sage-700">Intervention created.</p>
        )}
      </div>
    </form>
  );
}
