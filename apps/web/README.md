# Web App (Next.js)

This package hosts the Next.js application for early warning analytics, interventions, and GPT-powered insights.

## Stack
- Next.js 16.1 (App Router + Server Actions)
- React 19
- Clerk auth (Org-based multi-tenant context)
- Drizzle ORM (Postgres only)
- Tailwind CSS 4
- OpenAI SDK for GPT insights

## Local development

From the repo root:

```
bun install
bun run dev
```

Or from this directory:

```
bun install
bun run dev
```

## Environment variables

Copy `apps/web/.env.example` to `apps/web/.env` and set:

```
DATABASE_URL=postgresql://...
LOCAL_DATABASE_URL=postgresql://...
CLERK_SECRET_KEY=...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
ML_SERVICE_URL=https://your-ml-service
ML_SERVICE_API_KEY=your-ml-service-api-key
MAX_CSV_BYTES=5242880
SKIP_ML=false
```

Notes:
- `MAX_CSV_BYTES` also gates uploads in the app (defaults to 5MB if unset).
- `SKIP_ML=true` bypasses the ML service and returns empty predictions (useful for UI-only dev).
- `LOCAL_DATABASE_URL` is used by tests and `db:migrate` to keep a local copy in sync.
  Tests refuse to run without `LOCAL_DATABASE_URL` to avoid touching production data.

## Database migrations (Drizzle)

Run from repo root:

```
bun run db:generate
bun run db:migrate
```

Baseline an existing database once:

```
bun run db:baseline
```

`db:migrate` now runs migrations for both `DATABASE_URL` (remote) and `LOCAL_DATABASE_URL` (local).

## Tests

```
bun run test
```

Notes:
- Integration tests use `LOCAL_DATABASE_URL` when present.
- Coverage thresholds are configured in the Vitest configs; run with `--coverage` to enforce locally.
- Use `bun run test` (Vitest). `bun test` runs Bun's built-in runner and won't pick up the test harness.

## Key routes

UI:
- `/` - Landing
- `/sign-in` - Clerk sign-in
- `/sign-up` - Clerk sign-up
- `/dashboard` - Summary and stats
- `/upload` - CSV upload and analysis
- `/students` - Student roster
- `/interventions` - Plans and status updates
- `/insights` - GPT insights
- `/integrations` - Placeholder for LMS/SIS connectors
- `/settings` - Institution settings

API:
- `/api/health` - Health check
- `/api/events` - Server-sent events stream for realtime updates
- `/api/dashboard/stats` - Dashboard aggregates (query `institutionId` to override)
- `/api/data/all` - Data export (query: `institutionId`, `includeStudents`, `includeInsights`, `includeInterventions`)
- `/api/insights/latest` - Latest GPT insights per student
- `/api/insights/generate` - Generate a new GPT insight (POST with `{ studentId }`)
- `/api/students/[studentId]/interventions` - Student + intervention details
