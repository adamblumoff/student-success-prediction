# Student Success Platform (Next.js)

A full-stack Next.js application for early warning analytics, intervention planning, and GPT-powered insights for K-12 student success. The UI and backend are rebuilt on Next.js Server Actions with Clerk auth and Drizzle, while the ML model remains a dedicated Python service.

## What changed
- Frontend + backend now live in a single Next.js app (App Router + Server Actions).
- Authentication is fully managed by Clerk.
- Database access is via Drizzle to the production PostgreSQL instance.
- Python is only used for the ML model service.
- Legacy FastAPI app, templates, and tests have been removed.

---

## Architecture

```
Next.js (App Router)
  - Server Actions + Route Handlers
  - Clerk Auth
  - Drizzle ORM
  - UI (Tailwind)

Python ML Service
  - K12 Ultra Predictor (loaded from results/models)
```

---

## Required Environment Variables

Create a `.env` file in the repo root:

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

Important: This app expects the production Postgres instance as the single source of truth.

---

## Run the Next.js app

```
bun install
bun run dev
```
This starts the Next.js dev server.

---

## Run the ML Service (Python)

The ML service is separate and should be deployed on Railway as its own service.

```
python -m venv .venv
source .venv/bin/activate
pip install -r services/ml/requirements.txt
uvicorn services.ml.app:app --host 0.0.0.0 --port 9000
```

Set `ML_SERVICE_URL` to the deployed ML service endpoint.

---

## Deployment (Railway)

- Next.js app: deploy with Railpack and `Procfile`
- ML service: deploy a second Railway service with root directory `services/ml` and `services/ml/Procfile`

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
- Legacy FastAPI assets have been removed.
- If you need to re-enable local ML inference, run the ML service locally and point `ML_SERVICE_URL` to it.
