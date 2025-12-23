# Testing Guide

This repo uses unit + integration tests only (no E2E). Tests are split between the web app and the ML service.

## Web app (apps/web)

### Test layout
- Unit tests: `apps/web/tests/unit/**/*.test.ts(x)`
- Integration tests: `apps/web/tests/integration/**/*.test.ts`
- Shared helpers:
  - DB + migrations: `apps/web/tests/db.ts`
  - Fixtures: `apps/web/tests/fixtures.ts`
  - Unit setup: `apps/web/tests/setup.unit.ts`
  - Integration setup: `apps/web/tests/setup.integration.ts`

### Test runners
- Unit: `vitest` with `jsdom` environment
- Integration: `vitest` with `node` environment (single-threaded)

Config files:
- Unit: `apps/web/vitest.unit.config.ts`
- Integration: `apps/web/vitest.integration.config.ts`
- Shared config: `apps/web/vitest.shared.ts`

### Environment rules
- Integration tests **only** use `LOCAL_DATABASE_URL`.
- If `LOCAL_DATABASE_URL` is missing, integration tests will fail fast.
- Integration tests load env from `apps/web/.env` automatically.

### Commands
From repo root:
```
bun run test
bun run test:unit
bun run test:integration
```

### Coverage
Coverage thresholds are set in the Vitest configs. Run with `--coverage` to enforce locally.

---

## ML service (services/ml)

### Test layout
- Unit/integration tests live in `services/ml/tests/`.

### Test runner
- `pytest` + `pytest-cov`
- Config: `services/ml/pytest.ini`

### Commands
```
cd services/ml
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
pytest
```

---

## CI
GitHub Actions runs:
- Web unit + integration tests against a local Postgres service (`LOCAL_DATABASE_URL`).
- ML tests with pytest + coverage.

---

## Data safety
- Test code does not use `DATABASE_URL` in test mode.
- Only `LOCAL_DATABASE_URL` is used for integration tests.
