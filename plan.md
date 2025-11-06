# Refactor & Hardening Roadmap

## Objectives
- Remove unused/duplicate subsystems so the codebase has single sources of truth.
- Standardize configuration, authentication, and dependency management for predictable deployments.
- Strengthen testing/documentation to match the simplified architecture.

## Guiding Principles
1. **One way per concern** – single auth pipeline, single config loader, single dependency lock.
2. **Production-first defaults** – assume PostgreSQL + strict security; fail fast otherwise.
3. **Test-driven changes** – every behavioral change gets regression coverage (Python or JS).
4. **Document reality** – README/docs describe exactly what ships today.

## Workstreams & Tasks

### 1. Configuration & Database Layer
1.1 Re-introduce default Postgres host/port behavior in `src/mvp/database.py` (default to `localhost:5432` when user/password/name exist).  
1.2 Remove SQLite fallback branches; instead raise a descriptive error if PostgreSQL env is incomplete.  
1.3 Centralize env parsing in `src/mvp/config.py` (or new `config/runtime.py`) and have `DatabaseConfig` consume that.  
1.4 Add unit tests under `tests/config/test_database_config.py` covering common env combinations (complete Postgres, missing host, production without required vars).  
1.5 Update `.env` template(s) and documentation to reflect PostgreSQL-only support.

### 2. Authentication & Security Consolidation
2.1 Identify the active pipeline (likely `src/mvp/security.py` via DI) and remove the unused module (`src/mvp/simple_auth.py` or `simple_auth_clean.py`).  
2.2 Refactor FastAPI routers to import the surviving auth dependency only.  
2.3 Ensure `security_config` enforces no default API key/session secret in non-dev modes; add tests verifying failure on weak config.  
2.4 Update README + docs to stop publishing dev keys; add instructions for generating strong ones.  
2.5 Add startup self-check (e.g., `src/mvp/container.py`) that logs and aborts if required secrets/env vars are missing.

### 3. Services & Dependency Injection Cleanup
3.1 Move service singletons (Intervention system, predictors, GPT services) into `src/mvp/container.py` or a new `src/mvp/di.py`.  
3.2 Convert routers to request dependencies via the container rather than referencing module globals.  
3.3 Relocate mock data helpers (`src/mvp/services/*mock_data.py`) into `examples/` and gate any demo loaders behind explicit flags.  
3.4 Add lightweight interfaces/protocols in `src/mvp/services/__init__.py` to clarify what each service exposes.  
3.5 Provide tests or health checks that the container initializes successfully with mocked dependencies.

### 4. Testing & Tooling Alignment
4.1 Prune `package.json` scripts to suites that exist (`tests/components`, `tests/app-functionality.test.js`, etc.).  
4.2 Ensure Jest config points to actual directories; remove references to `tests/utils/test-runner.js` unless reimplemented.  
4.3 Add Python unit tests for config/security changes (from 1.4/2.3).  
4.4 Update `scripts/run_automated_tests.py` (or create) to run `pytest` + `npm test` + security checks in sequence.  
4.5 Document required commands in `README-TESTING.md` after cleanup.

### 5. Documentation Refresh
5.1 Merge overlapping structure docs (`DIRECTORY_STRUCTURE.md`, `CODEBASE_ROADMAP.md`) into concise sections within `README.md` or a new `docs/OVERVIEW.md`.  
5.2 Add “Current Limitations” and “Security Requirements” sections reflecting the PostgreSQL-only + strict auth posture.  
5.3 Update `docs/SECURITY_CHECKLIST.md` by removing resolved items and highlighting remaining P0 work.  
5.4 Ensure `AGENTS.md` (and related instructions) point to the new simplified workflows.

### 6. Dependency & Asset Management
6.1 Commit `package-lock.json` and stop ignoring it in `.gitignore`.  
6.2 Introduce `pip-tools` workflow: maintain `requirements.in` with top-level deps, auto-generate and commit `requirements.txt` lock.  
6.3 Add `npm audit` and `pip-audit` (or `safety`) steps to CI/tests script.  
6.4 Remove unused static assets/components; document any demo assets moved to `examples/`.  
6.5 Capture dependency update cadence (e.g., monthly check) in `README.md`.

## Suggested Sequence
1. Config/DB (Workstream 1) – fixes current regression and establishes Postgres-only baseline.  
2. Auth/Security (Workstream 2) – ensures all entry points share the same enforcement.  
3. Services/DI (Workstream 3) – reduces global state before adding more tests.  
4. Testing/Tooling (Workstream 4) – align scripts once architecture stabilizes.  
5. Documentation (Workstream 5) – reflect new truths immediately after code changes.  
6. Dependencies (Workstream 6) – lock versions once the tree is clean to avoid churn mid-refactor.

## Validation Checklist per Workstream
- **WS1**: `pytest tests/config -q` passing; manual attempt to start app without `DB_HOST` should fail with clear error.  
- **WS2**: Auth-protected endpoint rejects default key; startup logs confirm security checks.  
- **WS3**: `uvicorn src.mvp.mvp_api:app --reload` works; logs show container wiring each dependency once.  
- **WS4**: `npm test` + `pytest -q` succeed locally and in CI.  
- **WS5**: README matches actual commands; reviewers confirm no stale references.  
- **WS6**: `npm ci` + `pip install -r requirements.txt` reproducibly succeed; audits run clean or document exceptions.

## Open Questions / Pending Decisions
- Pick final home for configuration loader (extend `config_manager.py` or add new module).  
- Decide whether to script migrations for moving mock/demo data out of production imports.  
- Confirm CI environment (GitHub Actions vs other) for wiring new checks.

