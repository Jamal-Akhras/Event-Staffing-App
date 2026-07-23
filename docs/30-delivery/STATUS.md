# Project Status

## Last Updated
- Date: 2026-05-04

## Current Focus
- Web and mobile UI operational passes are complete; next step is visual polish/review against running apps.
- Backend production-readiness work has covered route ownership and shifted local DB config to Postgres.
- Preserve the future worker Match Feed idea in docs without implementing it yet.

## Implemented
- Booking lifecycle domain, API endpoints, transition guards, and tests.
- SQLAlchemy persistence, Alembic migrations, repository interfaces, Docker-backed local Postgres setup, and SQLite fallback.
- JWT auth with DEV_MODE header bypass for local web/mobile development.
- Shift posting, capacity tracking, duplicate application prevention, application approval/rejection, worker profiles, templates, recurring shift generation, messaging, and message history.
- Web React dashboard with routes for Dashboard, Shifts, Templates, Applications, Workers, Schedule, Analytics, and Settings.
- Mobile Expo worker app with Browse, Shifts, Profile, applications, messaging, and check-in/out flows.
- Backend service layer for shifts, applications, templates, messages, and booking lifecycle workflows.
- 2026-05-03 web UI pass: dashboard now prioritizes attention queue, open seats, 7-day coverage, and quick venue-manager actions.
- 2026-05-03 frontend structure pass: global CSS, Workers, and Schedule were split into smaller files; web source files are now under the 300-line rule.
- 2026-05-03 mobile UI pass: app entrypoint simplified to the real navigator, worker Browse/Shifts/Earnings/Profile screens refreshed, messaging cleaned up, and mobile source files are under the 300-line rule.
- 2026-05-03 worker feed-state pass: mobile Browse persists passed shifts per worker, supports undo, and backend exposes owned feed-state endpoints.
- 2026-05-03 backend hardening pass: applications, worker feed state, bookings, shifts, worker profiles/earnings, and message threads now enforce actor ownership for core worker/operator paths.
- 2026-05-03 migration reliability pass: Alembic resolves relative SQLite URLs against the repo root and can run from the repo root config path.
- 2026-05-04 Postgres migration pass: `.env`/`.env.example` now target Postgres, `psycopg` is the configured driver, Docker Compose provisions local Postgres, and SQLite moved to `.env.sqlite.example`.

## In Progress
- None.

## Next

### Backend Production Readiness
- Add Postgres-backed CI/integration tests and run migrations against Postgres in CI.
- Move no-show sweep and recurring generation from manual/route-triggered flows into a scheduler or worker.
- Add production observability: structured logs, request IDs, health details, error monitoring, and runbook notes.
- Wire production auth into web/mobile clients instead of relying on DEV_MODE headers.
- Model venues/accounts explicitly instead of relying only on string `operator_id` values.

### Frontend Product Work
- Visually review the upgraded web and mobile UIs and polish spacing, density, and responsive behavior.
- Revisit worker discovery after core UI polish; see `docs/40-future/worker_match_feed.md`.

## Known Issues
- Current relational ownership is enforced in routes, but the schema still needs first-class venue/account relationships before production.
- Background jobs still need a production scheduler/worker.

## Decisions
- Web-first MVP.
- Reliability-first workflows.
- Preserve the existing ocean green and warm paper palette.
- Keep worker Match Feed as a future enhancement, not part of the current UI upgrade.
- Use PostgreSQL for production and default local development; keep SQLite only for explicit lightweight fallback.
