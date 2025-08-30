# Repository Guidelines

## Project Structure & Module Organization
- `src/mvp/`: FastAPI app (`mvp_api.py`), modular API routers under `api/`, HTML templates, and static assets (`static/js`, `static/css`, `components/`).
- `src/models/`: ML pipelines for training/inference and feature engineering.
- `src/integrations/`: Connectors for Canvas, PowerSchool, and Google Classroom.
- `tests/`: Mixed suite — Python (pytest) and JS (Jest + jsdom).
- `scripts/`: Developer/CI utilities (e.g., `run_automated_tests.py`).
- `alembic/`: Database migrations and config. Also see `deployment/`, `docs/`, `data/`, `results/`.

## Build, Test, and Development Commands
- Backend setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run API locally: `python run_mvp.py` or `uvicorn src.mvp.mvp_api:app --reload --port 8001`
- JS tests: `npm install && npm test`
- Python tests: `pytest -q`
- Full suite + reports: `python scripts/run_automated_tests.py`
- DB migrations: `alembic upgrade head`

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indents, type hints; modules/functions snake_case; classes PascalCase; docstrings for public functions.
- JavaScript: ES modules, 2-space indents; variables camelCase; files kebab-case under `src/mvp/static/js` and `.../components`.
- Keep functions small and testable; place shared logic in `src/mvp/services` or `src/models`.

## Testing Guidelines
- Frameworks: PyTest (backend) and Jest (frontend, jsdom environment).
- Naming: Python `tests/test_*.py`; JS `tests/**/*.test.js`.
- Coverage: Jest thresholds 70% global and 85% for `src/mvp/static/js/core/*` (see `jest.config.js`). Target ≥70% for Python via `pytest --cov=src`.
- Run targeted suites: `npm run test:component`, `pytest tests/api -q`.

## Commit & Pull Request Guidelines
- Commits: Conventional Commits (e.g., `feat: add bulk status modal`, `fix(api): correct auth header check`).
- PRs: clear summary, linked issues, steps to test, screenshots for UI, and notes on security/config changes. Ensure `npm test`, `pytest`, and `alembic upgrade --sql` sanity outputs are green.

## Security & Configuration Tips
- Use a `.env`; set `MVP_API_KEY` and `ENVIRONMENT=development|production`. Never commit secrets.
- Follow `config/google_credentials_example.json` for OAuth setup; keep real credentials out of the repo.
- Review `docs/SECURITY_CHECKLIST.md` and `docs/ENCRYPTION_SYSTEM.md` before shipping.

