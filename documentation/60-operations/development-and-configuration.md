# Development and Configuration

## Local architecture

Normal development should use PostgreSQL for endpoint and schema work. In-memory repositories are useful for fast unit tests. SQLite is a lightweight fallback, not a concurrency or production-parity target.

## Prerequisites

- Python 3.11+
- Node.js 20
- Docker for the local PostgreSQL stack and production container checks
- Conda is supported through `environment.yml`, but a standard virtual environment also works

## Install

```powershell
conda env create -f environment.yml
conda activate event_staffing
python -m pip install -r requirements.txt

Set-Location apps/web
npm ci

Set-Location ../mobile
npm ci

Set-Location ../..
```

## Start PostgreSQL and migrate

```powershell
docker compose up -d postgres
python -m alembic -c apps/api/alembic.ini upgrade head
```

The compose database is exposed on host port `5433` with the local credentials documented in `.env.example`/Docker Compose. Run commands from the repository root so Python package imports resolve consistently.

## Start the apps

```powershell
# API on the configured local port
uvicorn apps.api.src.main:app --reload --host 127.0.0.1 --port 8001

# Background worker
python -m apps.api.src.worker

# Web, from apps/web
npm run dev

# Mobile, from apps/mobile
npx expo start
```

For a physical mobile device, bind the API to `0.0.0.0` and set `EXPO_PUBLIC_API_BASE` to a reachable local network address. Do not hard-code a developer machine IP into a release.

## Configuration groups

| Group | Important variables | Production rule |
|---|---|---|
| Environment | `ENVIRONMENT`, `DEV_MODE`, `USE_IN_MEMORY` | Production, dev mode false, in-memory false |
| Database | `DATABASE_URL` | Managed PostgreSQL required |
| Shared state | `REDIS_URL`, `TRUST_FORWARDED_FOR` | Redis required; trust proxy only when platform controls it |
| Authentication | `JWT_SECRET_KEY`, expiration settings, `OPERATOR_INVITE_CODES` | Unique 32+ character secret; invite list configured deliberately |
| Browser | `CORS_ORIGINS`, `WEB_BASE_URL` | Explicit HTTPS origins/URL |
| Email | `EMAIL_TRANSPORT`, `SMTP_*` | Real SMTP transport and sender |
| Storage | `STORAGE_BACKEND`, `OBJECT_STORAGE_*` | S3-compatible backend, never local |
| Observability | `SENTRY_DSN`, `SENTRY_RELEASE`, sampling | Production projects and release identifiers |
| Web build | `VITE_API_BASE`, `VITE_SENTRY_DSN` | Inject deployed HTTPS endpoints at build time |
| Mobile build | `EXPO_PUBLIC_API_BASE`, Expo/EAS credentials | Release endpoint and native push credentials |

Production startup fails rather than silently falling back when critical database, Redis, CORS, storage or JWT configuration is unsafe.

## Useful verification commands

```powershell
python -m pip check
python -m pytest -q
python -m alembic -c apps/api/alembic.ini current

Set-Location apps/web
npx tsc --noEmit
npm run build

Set-Location ../mobile
npx tsc --noEmit
npx expo install --check
```

The PostgreSQL CI leg sets `REQUIRE_POSTGRES_TESTS=true` so a skipped integration suite fails the intent of the job rather than producing false confidence.

## Demo accounts

The blank partner-demo script reads `DEMO_VENUE_EMAIL`, `DEMO_WORKER_EMAIL` and `DEMO_ACCOUNT_PASSWORD` from the environment, then creates or refreshes two logins without marketplace data. Credentials must never be committed or copied into screenshots.

## Migration workflow

1. Change SQLAlchemy models and write an explicit Alembic revision.
2. Test upgrade from the previous revision.
3. Test downgrade where supported.
4. Rebuild PostgreSQL from base to head.
5. Test legacy/backfilled data and constraints.
6. Consider lock duration and backward compatibility before production.

Do not edit generated context files manually. Update this documentation whenever a public contract, schema, flow, operational dependency or decision changes.
