export default function IntegrationsPage() {
  const integrations = [
    {
      name: 'Canvas',
      description: 'Sync assignments, grades, and attendance insights.',
      status: 'Not connected'
    },
    {
      name: 'PowerSchool',
      description: 'Pull SIS enrollment data and roster updates.',
      status: 'Not connected'
    },
    {
      name: 'Google Classroom',
      description: 'Import coursework, missing work, and activity signals.',
      status: 'Planned'
    }
  ];

  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs uppercase text-ink-400">Integrations</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink-50 text-balance">
          Connect your data systems
        </h1>
        <p className="mt-2 text-sm text-ink-300 text-pretty">
          Connect SIS and LMS systems to keep predictions and interventions refreshed.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {integrations.map((integration) => (
          <div key={integration.name} className="card space-y-4">
            <div>
              <p className="text-xs uppercase text-ink-400">Integration</p>
              <h2 className="mt-2 text-xl font-semibold text-ink-50 text-balance">
                {integration.name}
              </h2>
              <p className="mt-2 text-sm text-ink-300 text-pretty">
                {integration.description}
              </p>
            </div>
            <div className="flex items-center justify-between text-xs text-ink-400">
              <span>Status</span>
              <span className="badge badge-risk-medium">{integration.status}</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-200"
              >
                Connect
              </button>
              <button
                type="button"
                className="rounded-full border border-ink-700/60 px-4 py-2 text-xs font-semibold text-ink-400"
                disabled
              >
                View permissions
              </button>
            </div>
            <div className="rounded-2xl border border-ink-700/60 bg-ink-950/60 p-3 text-xs text-ink-400">
              Last sync: Not available
            </div>
          </div>
        ))}
      </div>
      <div className="bg-panel rounded-3xl p-6 text-sm text-ink-300 text-pretty">
        Prefer manual uploads? Use the Upload tab to submit CSVs until integrations are
        enabled.
      </div>
    </section>
  );
}
