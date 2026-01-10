'use client';

import { useActionState, useEffect } from 'react';
import { useFormStatus } from 'react-dom';
import { useMemo, useState } from 'react';
import { createInterventionAction, type InterventionActionState } from '@/lib/actions/interventions';
import { useAppData } from '@/components/app-data-provider';

const initialState: InterventionActionState = { status: 'idle' };

const templates = [
  {
    id: 'attendance-checkin',
    title: 'Attendance check-in',
    interventionType: 'Attendance outreach',
    description: 'Call home, identify barriers, and document an attendance support plan.',
    priority: 'high'
  },
  {
    id: 'academic-coaching',
    title: 'Academic coaching sprint',
    interventionType: 'Tutoring',
    description: 'Weekly tutoring for 4 weeks focused on missed assignments and study plans.',
    priority: 'medium'
  },
  {
    id: 'counselor-sync',
    title: 'Counselor check-in',
    interventionType: 'Counseling',
    description: '15-minute counseling session to review stressors and support needs.',
    priority: 'medium'
  }
];

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      className="rounded-full bg-sage-500 px-5 py-2 text-sm font-semibold text-slate-950"
      disabled={pending}
    >
      {pending ? 'Saving...' : 'Create intervention'}
    </button>
  );
}

type Defaults = {
  studentId?: number;
  title?: string;
  description?: string;
  interventionType?: string;
};

export default function InterventionForm({
  students,
  defaults,
  prefillStudentName,
  prefillSource
}: {
  students: Array<{ id: number; name: string | null; studentId: string }>;
  defaults?: Defaults;
  prefillStudentName?: string | null;
  prefillSource?: 'insight' | 'student' | null;
}) {
  const { selectedInstitutionId, markDashboardStatsStale } = useAppData();
  const [state, formAction] = useActionState(createInterventionAction, initialState);
  const [templateId, setTemplateId] = useState('');
  const [title, setTitle] = useState(() => defaults?.title ?? '');
  const [interventionType, setInterventionType] = useState(
    () => defaults?.interventionType ?? ''
  );
  const [description, setDescription] = useState(() => defaults?.description ?? '');
  const [priority, setPriority] = useState('medium');
  const [assignedRole, setAssignedRole] = useState('Counselor');
  const [assigneeName, setAssigneeName] = useState('');
  const [sendReminder, setSendReminder] = useState(true);
  const [studentId, setStudentId] = useState<number | undefined>(() => defaults?.studentId);

  const assignedTo = useMemo(() => {
    if (assigneeName.trim()) return `${assignedRole}: ${assigneeName.trim()}`;
    return assignedRole;
  }, [assignedRole, assigneeName]);

  const handleTemplateChange = (value: string) => {
    setTemplateId(value);
    const selected = templates.find((template) => template.id === value);
    if (!selected) return;
    setTitle(selected.title);
    setInterventionType(selected.interventionType);
    setDescription(selected.description);
    setPriority(selected.priority);
  };

  useEffect(() => {
    if (state.status !== 'success') return;
    if (!selectedInstitutionId) return;
    markDashboardStatsStale(selectedInstitutionId);
  }, [markDashboardStatsStale, selectedInstitutionId, state.status]);


  return (
    <form action={formAction} className="card space-y-6">
      <div>
        <p className="text-xs uppercase text-ink-400">New intervention</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-50 text-balance">
          Plan support
        </h2>
        {prefillStudentName && (
          <p className="mt-2 text-sm text-ink-300 text-pretty">
            {prefillSource === 'student'
              ? `Prefilled for ${prefillStudentName}.`
              : `Prefilled from GPT insight for ${prefillStudentName}.`}
          </p>
        )}
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-4">
          <label className="flex flex-col gap-2 text-sm text-ink-200">
            Student
            <select
              name="studentId"
              required
              value={studentId ?? ''}
              onChange={(event) => setStudentId(Number(event.target.value))}
              className="select-field rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-sm text-ink-100"
            >
              <option value="">Select student</option>
              {students.map((student) => (
                <option key={student.id} value={student.id}>
                  {student.name ?? `Student ${student.studentId}`}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm text-ink-200">
            Template
            <select
              value={templateId}
              onChange={(event) => handleTemplateChange(event.target.value)}
              className="select-field rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-sm text-ink-100"
            >
              <option value="">Custom plan</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.title}
                </option>
              ))}
            </select>
          </label>

          <div className="grid gap-3 md:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm text-ink-200">
              Title
              <input
                name="title"
                required
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-sm text-ink-100"
              />
            </label>
            <label className="flex flex-col gap-2 text-sm text-ink-200">
              Type
              <input
                name="interventionType"
                required
                placeholder="tutoring, counseling, etc."
                value={interventionType}
                onChange={(event) => setInterventionType(event.target.value)}
                className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-sm text-ink-100"
              />
            </label>
          </div>

          <label className="flex flex-col gap-2 text-sm text-ink-200">
            Description
            <textarea
              name="description"
              rows={4}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-sm text-ink-100"
            />
          </label>
        </div>

        <div className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm text-ink-200">
              Priority
              <select
                name="priority"
                value={priority}
                onChange={(event) => setPriority(event.target.value)}
                className="select-field rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-sm text-ink-100"
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </label>
            <label className="flex flex-col gap-2 text-sm text-ink-200">
              Status
              <select
                name="status"
                className="select-field rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-sm text-ink-100"
              >
                <option value="planned">Planned</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
              </select>
            </label>
          </div>

          <label className="flex flex-col gap-2 text-sm text-ink-200">
            Due date
            <input
              type="date"
              name="dueDate"
              className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-sm text-ink-100"
            />
          </label>

          <div className="grid gap-3 md:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm text-ink-200">
              Assigned role
              <select
                value={assignedRole}
                onChange={(event) => setAssignedRole(event.target.value)}
                className="select-field rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-sm text-ink-100"
              >
                <option value="Counselor">Counselor</option>
                <option value="Assistant Principal">Assistant Principal</option>
                <option value="Teacher">Teacher</option>
                <option value="Interventionist">Interventionist</option>
              </select>
            </label>
            <label className="flex flex-col gap-2 text-sm text-ink-200">
              Assigned to
              <input
                value={assigneeName}
                onChange={(event) => setAssigneeName(event.target.value)}
                placeholder="Name"
                className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-sm text-ink-100"
              />
            </label>
          </div>

          <label className="flex items-center gap-3 text-sm text-ink-200">
            <input
              type="checkbox"
              checked={sendReminder}
              onChange={(event) => setSendReminder(event.target.checked)}
              className="h-4 w-4 rounded border border-ink-600 bg-ink-950"
            />
            Send reminder before due date
          </label>
          <input type="hidden" name="assignedTo" value={assignedTo} />

          <div className="rounded-2xl border border-dashed border-ink-700/60 p-4 text-xs text-ink-400">
            {sendReminder
              ? 'Reminders will be scheduled 48 hours before the due date.'
              : 'Reminders are turned off for this plan.'}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <SubmitButton />
        {state.status === 'error' && <p className="text-sm text-rose-300">{state.error}</p>}
        {state.status === 'success' && (
          <p className="text-sm text-sage-200">Intervention created.</p>
        )}
      </div>
    </form>
  );
}
