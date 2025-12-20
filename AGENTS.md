# Repository Guidelines

## Project Structure & Module Organization
- `apps/web/`: Next.js app (App Router, Server Actions, Clerk auth, Drizzle ORM, Tailwind UI).
- `services/ml/`: Python ML service (FastAPI + K12 Ultra Predictor + model artifacts).

## Build, Test, and Development Commands
- Install deps: `bun install` (repo root; workspaces).
- Run web app: `bun run dev` (repo root).
- Build web app: `bun run build` (repo root).
- ML service (local):
  - `cd services/ml && python3 -m venv .venv && source .venv/bin/activate`
  - `python3 -m pip install -r requirements.txt`
  - `python3 -m uvicorn app:app --host 0.0.0.0 --port 9000`

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indents, type hints; snake_case for modules/functions, PascalCase for classes. Document public functions.
- TypeScript: ES modules, 2-space indents, camelCase variables.
- Shared web logic belongs in `apps/web/lib/` and `apps/web/db/`.

## Testing Guidelines
- Tests are currently being rebuilt; add new suites as needed.

## Commit & Pull Request Guidelines
- Use Conventional Commits (e.g., `feat(api): add risk endpoint`, `fix(ui): debounce search`).
- PR checklist: summary + testing steps, mention DB or config migrations, attach screenshots for UI updates, and note any security-sensitive changes.

## Security & Configuration Tips
- PostgreSQL is mandatory. Set `DATABASE_URL` or `DB_HOST/DB_USER/DB_PASSWORD/DB_NAME`; no SQLite fallback in the app.
- Always set Clerk keys, `OPENAI_API_KEY`, and `ML_SERVICE_URL`. Use `apps/web/.env` locally and never commit secrets.
