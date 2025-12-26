# Developer Guide - Event Staffing Platform

Complete guide for setting up, running, testing, and developing the Event Staffing Platform MVP.

## Table of Contents
- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Database Management](#database-management)
- [Authentication](#authentication)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)

---

## Project Overview

**Tech Stack:**
- **Backend:** FastAPI (Python)
- **Frontend Web:** React + Vite
- **Frontend Mobile:** React Native + Expo
- **Database:** SQLite (dev), PostgreSQL (production)
- **Authentication:** JWT with bcrypt

**Architecture:**
- Modular monolith
- Repository pattern for data access
- Domain-driven design
- Clean separation: domain logic in `packages/domain`, API in `apps/api`

---

## Prerequisites

### Required Software
- **Python:** 3.11+ (via Miniconda or Anaconda)
- **Node.js:** 18+ (for web and mobile apps)
- **Git:** For version control

### Installation

#### 1. Install Miniconda/Anaconda
Download from https://docs.conda.io/en/latest/miniconda.html

#### 2. Install Node.js
Download from https://nodejs.org/ (LTS version recommended)

---

## Initial Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Event_Staffing_App
```

### 2. Set Up Python Environment
```bash
# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate event_staffing

# Verify installation
python --version  # Should show Python 3.11+
```

### 3. Install Python Dependencies
```bash
# Dependencies are already specified in environment.yml and requirements.txt
# If you need to install additional packages:
pip install <package-name>

# Update environment after changes:
conda env update -f environment.yml --prune
```

### 4. Set Up Web Frontend
```bash
cd apps/web
npm install
cd ../..
```

### 5. Set Up Mobile Frontend
```bash
cd apps/mobile
npm install
cd ../..
```

### 6. Initialize Database
```bash
cd apps/api

# Run migrations to create database and tables
alembic upgrade head

# Verify migration status
alembic current
# Should show: 003_create_users_table (head)

cd ../..
```

### 7. Create Environment Variables (Optional)
```bash
# Copy example file
cp .env.example .env

# Edit .env and set your values:
# - JWT_SECRET_KEY (generate a secure random string for production)
# - DATABASE_URL (if using PostgreSQL)
```

---

## Running the Application

### Backend API

**Development mode (with auto-reload):**
```bash
conda activate event_staffing
cd apps/api
uvicorn apps.api.src.main:app --reload
```

The API will be available at: http://127.0.0.1:8000

**API Documentation:**
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### Web Frontend (Operator Interface)

**In a separate terminal:**
```bash
cd apps/web
npm run dev
```

The web app will be available at: http://localhost:5173

**Configuration:**
- API base URL is set via `VITE_API_BASE` environment variable
- Default in dev: http://127.0.0.1:8000

### Mobile App (Worker Interface)

**In a separate terminal:**
```bash
cd apps/mobile
npx expo start
```

**Running options:**
- Press `w` for web browser
- Press `a` for Android emulator
- Press `i` for iOS simulator (Mac only)
- Scan QR code with Expo Go app on your phone

**Configuration:**
- API base URL is set via `EXPO_PUBLIC_API_BASE`
- Default for physical device: http://192.168.10.131:8000 (update with your local IP)

---

## Testing

### Run All Tests
```bash
conda activate event_staffing

# Run all tests with verbose output
pytest -v

# Run specific test file
pytest apps/api/tests/test_auth.py -v

# Run specific test
pytest apps/api/tests/test_auth.py::test_register_worker_success -v
```

### Test Coverage
```bash
# Run tests with coverage report
pytest --cov=apps.api.src --cov=packages.domain

# Generate HTML coverage report
pytest --cov=apps.api.src --cov=packages.domain --cov-report=html
# Open htmlcov/index.html in browser
```

### Test Organization
- **Domain tests:** `packages/domain/tests/`
  - `test_booking.py` - Booking aggregate tests
  - `test_booking_state.py` - State machine tests
  - `test_reliability.py` - Reliability scoring tests

- **API tests:** `apps/api/tests/`
  - `test_health.py` - Health check endpoint
  - `test_auth.py` - Authentication endpoints
  - `test_user_repository.py` - User repository tests
  - `test_sqlalchemy_repositories.py` - SQLAlchemy repository tests
  - `test_reliability_and_sweep.py` - Reliability and no-show sweep integration tests

---

## Database Management

### Migrations

**View current migration:**
```bash
cd apps/api
alembic current
```

**Apply all pending migrations:**
```bash
alembic upgrade head
```

**Rollback one migration:**
```bash
alembic downgrade -1
```

**View migration history:**
```bash
alembic history
```

**Create a new migration:**
```bash
# After modifying models in apps/api/src/db/models.py
alembic revision -m "description of changes"
```

### Existing Migrations
1. **001_create_bookings** - Bookings table
2. **002_create_core_tables** - Shifts, applications, worker_profiles tables
3. **003_create_users_table** - Users table for authentication

### Database Location
- **SQLite (default):** `apps/api/event_staffing.db`
- **PostgreSQL:** Set `DATABASE_URL` in environment

### Inspecting the Database

**SQLite:**
```bash
cd apps/api
sqlite3 event_staffing.db

# List tables
.tables

# View schema
.schema users

# Query data
SELECT * FROM users;

# Exit
.quit
```

---

## Authentication

### User Roles
- **Worker:** Self-registers, applies to shifts, checks in/out
- **Operator:** Creates shifts, reviews applications, manages bookings
- **System:** Automated jobs (no-show sweep)

### Create an Operator Account
```bash
conda activate event_staffing
python -m apps.api.scripts.create_operator admin@example.com SecurePassword123
```

### Test Authentication

**Register a worker (via API):**
```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "worker@example.com", "password": "password123"}'
```

**Login (get JWT token):**
```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "worker@example.com", "password": "password123"}'
```

**Use JWT token for authenticated requests:**
```bash
# Save token from login response
TOKEN="<your-jwt-token-here>"

# Make authenticated request
curl http://127.0.0.1:8000/protected-endpoint \
  -H "Authorization: Bearer $TOKEN"
```

### Current Authentication State
- ✅ JWT authentication implemented (/auth/register, /auth/login)
- ✅ Old X-Actor-Role header system still working (for backward compatibility)
- ⏳ Existing endpoints need migration to JWT (future work)

---

## Development Workflow

### Code Organization
```
Event_Staffing_App/
├── packages/domain/          # Domain logic (pure Python)
│   ├── src/
│   │   ├── booking.py
│   │   ├── booking_state.py
│   │   ├── booking_state_machine.py
│   │   └── reliability.py
│   └── tests/
├── apps/api/                 # FastAPI backend
│   ├── alembic/             # Database migrations
│   ├── src/
│   │   ├── auth/            # JWT authentication
│   │   ├── db/              # Database models and config
│   │   ├── models/          # Domain models
│   │   ├── repositories/    # Data access layer
│   │   ├── services/        # Business logic services
│   │   ├── main.py          # FastAPI app
│   │   └── schemas.py       # API request/response schemas
│   ├── scripts/             # Admin scripts
│   └── tests/
├── apps/web/                # React web app (operator)
└── apps/mobile/             # React Native mobile app (worker)
```

### Making Changes

**1. Domain Logic Changes:**
- Edit files in `packages/domain/src/`
- Add tests in `packages/domain/tests/`
- Run tests: `pytest packages/domain/tests/ -v`

**2. API Changes:**
- Edit `apps/api/src/main.py` for endpoints
- Add tests in `apps/api/tests/`
- Run tests: `pytest apps/api/tests/ -v`

**3. Database Schema Changes:**
- Edit `apps/api/src/db/models.py`
- Create migration: `alembic revision -m "description"`
- Edit the generated migration file in `apps/api/alembic/versions/`
- Apply migration: `alembic upgrade head`

**4. Frontend Changes:**
- Web: Edit `apps/web/src/App.tsx`
- Mobile: Edit `apps/mobile/App.tsx`
- Changes are auto-reloaded in dev mode

### Documentation Discipline (MANDATORY)
After every meaningful change, update:
1. `README.md` - High-level status
2. `docs/30-delivery/STATUS.md` - Implementation status
3. `docs/30-delivery/DEVLOG.md` - Append change log entry

**Failure to update docs is a bug.**

---

## Background Jobs

### No-Show Sweep Job

**Manual execution:**
```bash
conda activate event_staffing
cd apps/api
python -m apps.api.src.jobs.run_no_show_sweep
```

**What it does:**
- Finds bookings in CONFIRMED state where check-in window has expired
- Marks them as NO_SHOW
- Updates worker reliability scores

**Schedule (future):**
- Currently manual
- Should run every 15 minutes via cron/scheduler in production

---

## Troubleshooting

### Common Issues

**1. "ModuleNotFoundError: No module named 'apps'"**
- **Cause:** Running from wrong directory or path not set
- **Fix:** Ensure you're in the project root and have activated the conda environment

**2. "alembic.util.exc.CommandError: Can't locate revision..."**
- **Cause:** Alembic env.py import path issue
- **Fix:** Already fixed in `apps/api/alembic/env.py` (parents[3] not parents[2])

**3. "Database is locked"**
- **Cause:** Multiple processes accessing SQLite database
- **Fix:** Close all connections or use PostgreSQL for concurrent access

**4. API returns 401 Unauthorized**
- **Cause:** Missing or invalid JWT token
- **Fix:** Ensure you've included `Authorization: Bearer <token>` header

**5. Web/Mobile app can't connect to API**
- **Cause:** API not running or wrong URL
- **Fix:**
  - Ensure API is running on http://127.0.0.1:8000
  - Check VITE_API_BASE (web) or EXPO_PUBLIC_API_BASE (mobile)
  - For mobile on physical device, use your computer's local IP

**6. Tests failing with "fixture not found"**
- **Cause:** pytest not finding test fixtures
- **Fix:** Ensure you're in the project root when running pytest

### Reset Database (Development Only)
```bash
cd apps/api
rm event_staffing.db  # Delete database file
alembic upgrade head  # Recreate from migrations
```

### View API Logs
API logs are printed to console where uvicorn is running. Watch for:
- Request/response details
- SQL queries (if `echo=True` in database.py)
- Error tracebacks

---

## Next Steps

### Immediate (Required for production):
1. Update web and mobile UIs to use JWT authentication
2. Migrate existing endpoints from X-Actor-Role to JWT validation
3. Set up automated no-show sweep scheduler
4. Configure production database (PostgreSQL)

### Future Enhancements:
- Email/SMS notifications
- Payment integration (Stripe)
- Badge system for workers
- Advanced reliability features
- Admin dashboard

---

## Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Docs:** https://react.dev/
- **React Native Docs:** https://reactnative.dev/
- **Expo Docs:** https://docs.expo.dev/
- **Alembic Docs:** https://alembic.sqlalchemy.org/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/

---

## Getting Help

1. Check this guide first
2. Review existing tests for examples
3. Check `docs/` folder for specifications:
   - `docs/00-idea/idea.md` - Product concept
   - `docs/10-specs/state_machine_spec.md` - State machine (authoritative)
   - `docs/30-delivery/STATUS.md` - Current status
   - `docs/30-delivery/DEVLOG.md` - Development history

4. For issues, create a ticket with:
   - What you were trying to do
   - What happened
   - Error messages
   - Steps to reproduce
