
# Event Staffing Platform – MVP

Reliability-first, operationally focused event staffing platform.

This repository is designed to be:
- Simple (KISS)
- Minimal (YAGNI)
- Correct and maintainable (SOLID)

Current status:
- Domain state machine and booking aggregate implemented
- FastAPI booking lifecycle endpoints with tests
- OpenAPI response schemas for booking endpoints
- React web shell with API health status
- Persistence layer stubs for repository + models
- SQLAlchemy repository adapter and shared API schemas
- Minimal booking UI for create/load/transition
- Booking list endpoint and recent bookings UI
- Worker applications and operator approvals
- Shift posting/listing and worker browsing
- Worker profile editing and operator public views
- Mobile bottom nav respects safe-area
- Mobile shifts include applications tab
- API schemas cleaned up
- Expo worker app scaffold with minimal status screen
- Worker mobile app polls bookings every 15 seconds
- Root .gitignore added for repo hygiene
- CORS allowlist for local Vite dev

API config:
- Default repo is in-memory; set `DATABASE_URL` to use SQLAlchemy (SQLite or Postgres).
- Set `USE_IN_MEMORY=true` to force in-memory even if `DATABASE_URL` is set.
- API endpoints require `X-Actor-Role` header: `operator`, `worker`, or `system`.

Migrations:
- Alembic config lives in `apps/api/alembic.ini`.
- Run migrations from `apps/api`: `alembic upgrade head`

Conda setup:
- Create env: `conda env create -f environment.yml`
- Activate: `conda activate event_staffing`
- Update deps after changes: `conda env update -f environment.yml --prune`

See docs/ for authoritative specifications.









