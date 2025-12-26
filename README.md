
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
- SQLAlchemy repositories for shifts, applications, and worker profiles
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
- Web UI refreshed with premium styling and updated layout
- Reliability scoring based on booking outcomes
- System no-show sweep endpoint and tests

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

Running:
- API (FastAPI): from `apps/api` run `uvicorn apps.api.src.main:app --reload`
- Web (Vite): from `apps/web` run `npm install` then `npm run dev`
- Mobile (Expo): from `apps/mobile` run `npm install` then `npx expo start`
- Web API base URL: set `VITE_API_BASE` (example: `http://127.0.0.1:8000`)
- Web dev default: if `VITE_API_BASE` is unset, the web app uses `http://127.0.0.1:8000` in dev mode
- No-show sweep job: from `apps/api` run `python -m apps.api.src.jobs.run_no_show_sweep`

API flows:
- See `docs/api_flows.md` for web/mobile/backend flow diagram

Mobile polling:
- The mobile app refreshes bookings/shifts/applications every 15 seconds when `EXPO_PUBLIC_API_BASE` is set
- Mobile default API base (physical device): `http://192.168.10.131:8000`
- Mobile polling skips overlapping requests to avoid piling up

See docs/ for authoritative specifications.









