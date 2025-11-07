# Repository Guidelines

## Project Structure & Module Organization
- `src/mvp/`: FastAPI app (`mvp_api.py`), modular routers (`api/`), HTML templates, static assets, middleware, and DI container wiring.
- `src/models/`: ML pipelines plus feature engineering code.
- `examples/mock_data/`: Canvas/PowerSchool/Google Classroom demo generators (used by import endpoints only in demo mode).
- `tests/`: Pytest (backend) + Jest (frontend) suites.
- `scripts/`, `deployment/`, `docs/`, `results/`: operational helpers, infra configs, and analysis artifacts.
- `alembic/`: database migrations; always run `alembic upgrade head` after schema changes.

## Build, Test, and Development Commands
- Python env: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run API: `python run_mvp.py` (assumes PostgreSQL via `DATABASE_URL` or `DB_*` vars)
- JS deps & tests: `npm install && npm test` (Jest default suite) or `npm run test:working` (focused smoke set)
- Backend tests: `PYTHONPATH=. pytest tests/api tests/config -q` (add other folders as needed)
- Database migrations: `alembic upgrade head`

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indents, type hints; snake_case for modules/functions, PascalCase for classes. Document public functions.
- JavaScript: ES modules, 2-space indents, camelCase variables, kebab-case filenames under `src/mvp/static/js` and `.../components`.
- Shared logic belongs in DI-backed services (`src/mvp/container.py` registration, service implementations under `src/mvp/services/`) or `src/models/`.

## Testing Guidelines
- Pytest focuses on API/integration coverage; keep tests deterministic by using temporary SQLite files (never the live DB).
- Jest runs via `npm test` (full) or `npx jest <pattern>` for targeted suites. Frontend helpers live in `tests/utils/test-setup.js`.
- Follow naming: Python `tests/test_*.py`, JS `tests/**/*.test.js`.
- Minimum expectations: keep backend smoke suites green (`pytest tests/api -q`) and ensure `npm run test:working` passes before pushing.

## Commit & Pull Request Guidelines
- Use Conventional Commits (e.g., `feat(api): add risk endpoint`, `fix(ui): debounce search`).
- PR checklist: summary + testing steps, mention DB or config migrations, attach screenshots for UI updates, and note any security-sensitive changes. Run `npm test`, targeted pytest suites, and `alembic upgrade head` (or `--sql`) before merging.

## Security & Configuration Tips
- PostgreSQL is mandatory. Set `DATABASE_URL` or `DB_HOST/DB_USER/DB_PASSWORD/DB_NAME`; no SQLite fallback in the app.
- Always set `MVP_API_KEY`, `SESSION_SECRET`, and `ENVIRONMENT`. Use `.env` locally and never commit secrets.
- OAuth/Google setup follows `config/google_credentials_example.json`; keep real credentials out of the repo.
- Review `docs/SECURITY_CHECKLIST.md` and `docs/ENCRYPTION_SYSTEM.md` before shipping features that touch data flows or auth.
