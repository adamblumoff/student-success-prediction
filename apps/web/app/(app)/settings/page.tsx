import {
  createInstitution,
  updateInstitution,
  updateTenantSettings
} from '@/lib/actions/settings';
import { loadTenantSummary } from '@/lib/data/tenant';
import SubmitButton from '@/components/submit-button';

export default async function SettingsPage() {
  const { district, institutions } = await loadTenantSummary();

  return (
    <section className="space-y-6">
      <div className="card">
        <p className="text-xs uppercase text-ink-400">Settings</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink-50 text-balance">
          Workspace preferences
        </h1>
        <p className="mt-2 text-sm text-ink-300 text-pretty">
          Update the district name shown across the platform.
        </p>
      </div>

      <form action={updateTenantSettings} className="card space-y-6">
        <div className="space-y-2">
          <label className="text-xs uppercase text-ink-500">District name</label>
          <input
            name="districtName"
            defaultValue={district?.name ?? ''}
            placeholder="District name"
            className="w-full rounded-2xl border border-ink-700/60 bg-ink-950/60 px-4 py-3 text-sm text-ink-100"
          />
        </div>
        <SubmitButton
          label="Save changes"
          pendingLabel="Saving..."
          className="rounded-full border border-ink-700/60 px-5 py-3 text-xs font-semibold uppercase text-ink-100 hover:border-ink-500/70 hover:bg-ink-800/70"
        />
      </form>

      <div className="card space-y-6">
        <div>
          <p className="text-xs uppercase text-ink-400">Schools</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink-50 text-balance">
            Manage institutions
          </h2>
          <p className="mt-2 text-sm text-ink-300 text-pretty">
            Create and edit schools in your district. The first school is used when no
            selection is active.
          </p>
        </div>

        <div className="space-y-4">
          {institutions.map((item) => (
            <div key={item.id} className="rounded-2xl border border-ink-800/60 bg-ink-950/40 p-4">
              <form action={updateInstitution} className="grid gap-3 md:grid-cols-3">
                <input type="hidden" name="institutionId" value={item.id} />
                <div className="space-y-2">
                  <label className="text-xs uppercase text-ink-500">Name</label>
                  <input
                    name="name"
                    defaultValue={item.name}
                    className="w-full rounded-2xl border border-ink-700/60 bg-ink-950/60 px-3 py-2 text-sm text-ink-100"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs uppercase text-ink-500">Code</label>
                  <input
                    name="code"
                    defaultValue={item.code}
                    className="w-full rounded-2xl border border-ink-700/60 bg-ink-950/60 px-3 py-2 text-sm text-ink-100"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs uppercase text-ink-500">Type</label>
                  <input
                    name="type"
                    defaultValue={item.type}
                    className="w-full rounded-2xl border border-ink-700/60 bg-ink-950/60 px-3 py-2 text-sm text-ink-100"
                  />
                </div>
                <div className="flex flex-wrap items-center gap-2 md:col-span-3">
                  <SubmitButton
                    label="Save"
                    pendingLabel="Saving..."
                    className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold uppercase text-ink-200"
                  />
                </div>
              </form>
            </div>
          ))}
        </div>

        <form action={createInstitution} className="grid gap-3 md:grid-cols-3">
          <div className="space-y-2">
            <label className="text-xs uppercase text-ink-500">New school</label>
            <input
              name="name"
              placeholder="School name"
              className="w-full rounded-2xl border border-ink-700/60 bg-ink-950/60 px-3 py-2 text-sm text-ink-100"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase text-ink-500">Code</label>
            <input
              name="code"
              placeholder="SCH-001"
              className="w-full rounded-2xl border border-ink-700/60 bg-ink-950/60 px-3 py-2 text-sm text-ink-100"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs uppercase text-ink-500">Type</label>
            <input
              name="type"
              defaultValue="K12"
              className="w-full rounded-2xl border border-ink-700/60 bg-ink-950/60 px-3 py-2 text-sm text-ink-100"
            />
          </div>
          <div className="md:col-span-3">
            <SubmitButton
              label="Add school"
              pendingLabel="Adding..."
              className="rounded-full border border-ink-700/60 px-5 py-3 text-xs font-semibold uppercase text-ink-100 hover:border-ink-500/70 hover:bg-ink-800/70"
            />
          </div>
        </form>
      </div>
    </section>
  );
}
