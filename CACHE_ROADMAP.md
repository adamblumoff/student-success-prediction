# Cache & Invalidation Roadmap

## Scope
Extend per-institution caching + invalidation to all data-driven routes (students, interventions, insights, dashboard) with:
- versioned API responses
- stale flags + targeted invalidation via SSE/local mutations
- cache persistence across tabs (localStorage + storage events)

## Milestones
- [x] Add `version` to API responses for students/interventions/insights
- [x] Add integration tests to verify version changes
- [x] Extend AppDataProvider with per-dataset cache + stale state
- [x] Add localStorage persistence + cross-tab sync
- [x] Update route clients to skip fetches when cache is fresh
- [x] Wire mutation handlers to mark cache stale
- [x] Update docs

## Datasets
- Students
- Interventions
- Insights
- Dashboard stats

## Invalidation Sources
- SSE events (`data:mutation`)
- Local mutations:
  - Uploads
  - Student delete / counselor assign
  - Intervention create/update/delete
  - Insight generate

## Notes / Decisions
- Do NOT include predictions table in versioning (use students.latestPredictionDate + updated_at)
- Do NOT increment version for identical content
- Persist caches across tabs; clear on real sign-out

## Progress Log
- 2026-01-12: Created roadmap
- 2026-01-12: Implemented versions, persistence, stale invalidation, and tests
