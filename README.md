# Student Success Platform (Monorepo)

A monorepo that hosts a full-stack Next.js application for early warning analytics, intervention planning, and GPT-powered insights, plus a dedicated Python ML service for the K-12 model.

## Repository layout

```
apps/
  web/           # Next.js app (App Router + Server Actions)
services/
  ml/            # Python ML service (FastAPI + K12 model)
```

## Core stack
- Next.js App Router + Server Actions
- Clerk auth
- Drizzle ORM (Postgres only)
- Tailwind CSS
- Python ML service (K12 Ultra Predictor)

---

## Architecture

```
Next.js app (apps/web)
  - Server Actions + Route Handlers
  - Clerk Auth
  - Drizzle ORM
  - UI (Tailwind)

Python ML Service (services/ml)
  - K12 Ultra Predictor (loaded from services/ml/results/models)
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
```

Important: The app expects the production Postgres instance as the single source of truth.

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

The ML service is separate and should be deployed on Railway as its own service.

```
cd services/ml
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 9000
```

Set `ML_SERVICE_URL` to the deployed ML service endpoint.

---

## Deployment (Railway)

- Next.js app: repo root using `Procfile` (runs `apps/web`)
- ML service: root directory `services/ml` using `services/ml/Procfile`

Both services should point to the same production PostgreSQL instance.

---

## Routes

- `/` - Landing
- `/dashboard` - Summary and stats
- `/upload` - CSV upload and analysis
- `/students` - Student roster
- `/interventions` - Plans and status updates
- `/insights` - GPT insights
- `/integrations` - Placeholder for LMS/SIS connectors

---

## Notes
- No legacy tests are retained; new test suites will be introduced later.
- If you need to re-enable local ML inference, run the ML service locally and point `ML_SERVICE_URL` to it.
- Student deletions are hard deletes today; plan to add soft-delete + restore in a future iteration.
- Counselor assignment is stored as free text on `students.assigned_counselor`; plan to normalize to a counselor/user model later.
- Roster interventions are single-student only for now; bulk interventions will be added later.
