# Postgres Local Setup

Use Postgres for normal backend development and staging parity. SQLite is now only the lightweight fallback for quick demos/tests.

## Create The Database

From an Anaconda Prompt at the repo root:

```powershell
conda activate event_staffing
python -m pip install -r requirements.txt
docker compose up -d postgres
docker compose ps
python -m alembic -c apps/api/alembic.ini upgrade head
python -m apps.api.scripts.seed_demo_data
```

The compose service creates this database automatically on first startup:

```text
database: event_staffing
user: event_staffing
password: event_staffing_local_password
host: localhost
host port: 5433
container port: 5432
```

The matching app URL is:

```text
postgresql+psycopg://event_staffing:event_staffing_local_password@localhost:5433/event_staffing
```

## Useful Commands

Check Postgres health:

```powershell
docker compose exec postgres pg_isready -U event_staffing -d event_staffing
```

Open `psql` inside the container:

```powershell
docker compose exec postgres psql -U event_staffing -d event_staffing
```

Reset the local Postgres database:

```powershell
docker compose down -v
docker compose up -d postgres
python -m alembic -c apps/api/alembic.ini upgrade head
python -m apps.api.scripts.seed_demo_data
```

Run the API against Postgres:

```powershell
uvicorn apps.api.src.main:app --reload --host 127.0.0.1 --port 8001
```

## SQLite Fallback

To switch back temporarily, copy values from `.env.sqlite.example` into `.env`, then run:

```powershell
python -m alembic -c apps/api/alembic.ini upgrade head
python -m apps.api.scripts.seed_demo_data
```
