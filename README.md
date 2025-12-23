# Student Success Platform (Monorepo)

A monorepo that hosts a full-stack Next.js application for early warning analytics, intervention planning, and GPT-powered insights, plus a dedicated Python ML service for the K-12 risk model.

## Repository layout

```
apps/
  web/           # Next.js app (App Router + Server Actions)
services/
  ml/            # Python ML service (FastAPI + K12 models)
```

## Core stack
- Next.js 16.1 (App Router + Server Actions)
- React 19
- Clerk auth (Org-based multi-tenant context)
- Drizzle ORM (Postgres only)
- Tailwind CSS 4
- OpenAI SDK for GPT insights
- Python ML service (FastAPI + K12 Success Predictor)

---

## Architecture

```
Next.js app (apps/web)
  - Server Actions + Route Handlers
  - Clerk Auth (orgs map to districts)
  - Drizzle ORM (Postgres)
  - Realtime SSE events via /api/events
  - UI (Tailwind)

Python ML Service (services/ml)
  - K12 Success Predictor (loaded from services/ml/results/models/k12)
  - /predict endpoint for CSV uploads
```

---

## Required Environment Variables

Create a `.env` file in `apps/web/` (see `apps/web/.env.example`):

```
DATABASE_URL=postgresql://...
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
- `MAX_CSV_BYTES` also gates uploads on the web app (defaults to 5MB if unset).
- `SKIP_ML=true` bypasses ML calls and returns empty predictions (useful for UI-only dev).
- The app expects the production Postgres instance as the single source of truth.

Create a `.env` file in `services/ml/` for the ML service:

```
ML_SERVICE_API_KEY=your-ml-service-api-key
ML_REQUIRE_API_KEY=true
MAX_CSV_BYTES=5242880
MAX_CSV_ROWS=20000
RATE_LIMIT_PER_MIN=60
K12_MODEL_FLAVOR=default
K12_MODELS_DIR=./results/models/k12
```

---

## Run the Next.js app

```
bun install
bun run dev
```
This starts the Next.js dev server.

---

## Database migrations (Drizzle)

Migrations live in `apps/web/db/migrations`.

Generate a migration after editing `apps/web/db/schema.ts`:

```
bun run db:generate
```

If the database already exists (e.g., production), baseline once so Drizzle won't try to create tables:

```
bun run db:baseline
```

Apply migrations to the configured Postgres database:

```
bun run db:migrate
```

Both commands read `DATABASE_URL` from `apps/web/.env`.

---

## Run the ML Service (Python)

The ML service is separate and should be deployed as its own service.

Local dev with existing model artifacts:

```
cd services/ml
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m uvicorn app:app --host 0.0.0.0 --port 9000
```

Training-on-start (matches `services/ml/Procfile`):

```
cd services/ml
./start.sh
```

`start.sh` downloads public datasets into `services/ml/data`, builds a mixed dataset, trains models,
and writes artifacts to `services/ml/results/models/k12` before starting Uvicorn.

Set `ML_SERVICE_URL` and `ML_SERVICE_API_KEY` in the web app environment to the deployed ML service values.

---

## Deployment (Railway)

- Next.js app: root directory `apps/web` using `apps/web/Procfile`
- ML service: root directory `services/ml` using `services/ml/Procfile`
- Monorepo Procfile at repo root (`Procfile`) starts the web app if needed

Both services should point to the same production PostgreSQL instance.

---

## Routes

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

---

## Notes
- No legacy tests are retained; new test suites will be introduced later.
- If you need to re-enable local ML inference, run the ML service locally and point `ML_SERVICE_URL` to it.
- Student deletions are hard deletes today; plan to add soft-delete + restore in a future iteration.
- Counselor assignment is stored as free text on `students.assigned_counselor`; plan to normalize to a counselor/user model later.
- Roster interventions are single-student only for now; bulk interventions will be added later.
