
# Project Status

## Last Updated
- Date: 2025-12-27

## Implemented
- Booking state machine (domain)
- Basic domain tests
- Booking aggregate with transition guards
- FastAPI app skeleton with health check
- API tests (health check)
- Booking lifecycle endpoints (request/confirm/check-in/out/approve/pay/no-show/cancel)
- Booking domain and API tests for edge cases
- Web MVP shell (React + Vite)
- Minimal booking UI (create/load/transition)
- Booking list endpoint and recent bookings UI
- UI actions disabled based on server-allowed transitions
- Expo worker app scaffold with minimal status screen
- Root .gitignore added to keep the repo clean
- API repository dependency injection and DB config hook
- Alembic migrations scaffold + initial bookings table
- Worker app bookings list and check-in/out actions
- Worker app booking detail screen (timestamps + check-in window)
- Role-based API access stub (X-Actor-Role)
- Conda environment and requirements added
- Persistence layer stubs (SQLAlchemy models + repository interface)
- OpenAPI response models for booking endpoints
- API schemas split into dedicated module
- SQLAlchemy booking repository implementation

- CORS allowlist for local Vite dev
- Worker app polling every 15 seconds
- Worker applications API and approval flow
- Operator UI for reviewing applications
- Worker app application form
- API schema definitions cleaned
- Shift posting and listing endpoints
- Mobile tabbed navigation (Browse, Shifts, Profile)
- Worker shift apply sheet with details
- Worker profile API (public vs private)
- Mobile bottom navigation pinned
- Operator view of worker profiles
- Worker profile editing and public operator view
- Mobile bottom navigation fixed to screen
- Mobile nav respects safe-area inset
- Worker profile API and editing
- My applications tab in mobile shifts
- Mobile top bar respects safe-area inset
- Reliability scoring from booking outcomes (domain + API)
- System no-show sweep endpoint and background job runner
- Web UI refreshed with premium styling
- SQLAlchemy persistence for shifts, applications, and worker profiles
- No-show sweep service and runnable job
- Service layer for booking operations (reliability refresh, no-show sweep)
- API flows diagram added
- API flows diagram labels fixed
- Reliability domain logic and tests
- Comprehensive tests for reliability scoring and no-show sweep
- JWT-based authentication system with bcrypt password hashing
- User registration and login endpoints
- User model and repository (interface + SQLAlchemy + in-memory)
- Database migration 003 for users table
- Operator account creation script
- Authentication test suite
- Multi-worker shift capacity (workers_needed/workers_filled tracking)
- Database migration 004 for shift capacity fields
- Shift status auto-update to "filled" when capacity reached
- Application validation to prevent overstaffing
- Comprehensive tests for shift capacity functionality

## In Progress
- None

## Next
- Update web and mobile UIs to use JWT authentication
- Migrate existing endpoints from X-Actor-Role to JWT validation
- Automated no-show sweep scheduler
- Basic notification system (email/SMS)
- WebSocket event stream for mobile shift updates (future)

## Notes
- Mobile app default API base set for physical device testing (LAN IP)
- Mobile polling guards against overlapping requests

## Decisions
- Web-first MVP
- Reliability over discovery









