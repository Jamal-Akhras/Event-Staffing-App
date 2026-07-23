# Operational Runbook

Owner placeholders:
- Product/engineering owner: [OWNER NAME]
- On-call contact: [ON-CALL PHONE OR SLACK]
- Cloud account owner: [CLOUD OWNER]
- Privacy/security contact: [PRIVACY CONTACT EMAIL]

## Service Level Objectives (SLO)

MVP targets — defensible in sales conversations until measurement is in place.

- **Availability**: 99.0 % monthly for the API. Includes planned maintenance windows with prior notice.
- **API latency**: p95 under 800 ms for cached read endpoints, p95 under 2 s for write endpoints.
- **Error rate**: under 1 % of requests return 5xx over any rolling 24 h window.
- **Background jobs**: no-show sweep runs every 15 min; missed runs are tolerated up to 60 min before paging.
- **Incident response**: acknowledge within 30 min during business hours, 2 h outside business hours.

Targets graduate to contractual SLAs once a customer signs a paid contract. Numbers above are starting points — adjust before signing.

## Alerts and paging

- Errors are reported to Sentry (`SENTRY_DSN` set in API + worker; `VITE_SENTRY_DSN` set at web build time).
- Sentry projects: `event-staffing-api`, `event-staffing-worker`, `event-staffing-web`. Add release tags via CI once tagging is configured.
- Alert rules to configure in Sentry:
  - API 5xx rate > 1 % over 5 min
  - Worker job exception (any) — page immediately
  - New issue marked priority=high
  - Forgot-password endpoint spike > 30/min (credential-stuffing signal)
- Routing: Sentry → `[ON-CALL PHONE OR SLACK]`. Configure a Slack integration or PagerDuty bridge before launch.

## Deploy

1. Confirm the target environment uses `.env.production.example` values in the secret store:
   - `ENVIRONMENT=production`
   - `DEV_MODE=false`
   - `JWT_SECRET_KEY` is unique and at least 32 characters
   - `DATABASE_URL` points to managed Postgres
   - `CORS_ORIGINS` includes only approved web origins
   - `SENTRY_DSN` and `VITE_SENTRY_DSN` set to the production projects
2. Build the image from the repo root Dockerfile.
3. Run database migrations before serving traffic:

   ```bash
   # bash / Linux container
   python -m alembic -c apps/api/alembic.ini upgrade head
   ```

   ```powershell
   # PowerShell / Windows dev host
   python -m alembic -c apps/api/alembic.ini upgrade head
   ```

4. Start exactly one API service and one scheduler worker:
   - API: `uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000`
   - Worker: `python -m apps.api.src.worker`
5. Check `/health` returns `{"status":"ok"}` and confirm web/mobile API base URLs point at the production API.

## Backups

- Database: managed Postgres automated daily backups retained for [RETENTION PERIOD].
- Uploads: persist `/app/apps/api/uploads` to durable object storage or a mounted volume backed up daily.
- Backup owner: [BACKUP OWNER].
- Restore drill: run at least quarterly in staging using the latest backup snapshot.

## Disaster recovery

Single-region MVP. Multi-region failover is on the roadmap, not implemented.

- **RTO target**: under 4 h from declaration to a fresh region serving traffic.
- **RPO target**: under 24 h (matches daily backup cadence).
- DR procedure:
  1. Provision a new managed Postgres instance in the recovery region.
  2. Restore the most recent automated backup snapshot.
  3. Apply pending Alembic migrations against the restored DB.
  4. Re-deploy the API and worker images pointing at the new `DATABASE_URL`.
  5. Re-upload the latest backed-up `uploads/` snapshot to the new storage bucket.
  6. Update DNS / load-balancer to the new region.
- Annual DR rehearsal: schedule with [CLOUD OWNER].

## Rollback

1. Stop new deploy rollout.
2. Revert API and worker to the previous known-good image.
3. If a migration is backward-compatible, do not downgrade the database during the incident.
4. To find the previous migration revision:

   ```bash
   python -m alembic -c apps/api/alembic.ini history | head -10
   # the second entry from the top is the previous revision
   ```

5. If a migration must be reverted, run the Alembic downgrade only after confirming data loss risk:

   ```bash
   python -m alembic -c apps/api/alembic.ini downgrade <previous_revision>
   ```

6. Confirm `/health`, login, shift listing, application review, and worker browse still work.

## Monitoring And Logs

- API health: `/health`.
- API logs: platform container logs for `event-staffing-api`.
- Worker logs: platform container logs for `event-staffing-worker`.
- Database health: managed Postgres dashboard or `pg_isready`.
- Sentry: triage by project. Inbox → assign → fix or suppress with reason.
- Alert triggers: API health failures, worker crash loop, migration failure, database connection errors, elevated 5xx responses, failed login spikes.

## Security incident — credential or secret leak

If a secret leaks (JWT, DB password, Sentry DSN, API key, etc.):

1. **Contain**: revoke or rotate the leaked secret in its source-of-truth (Stripe dashboard, Postmark dashboard, secret store, etc.).
2. **Rotate**:
   - `JWT_SECRET_KEY`: generate a new 48+ char secret, deploy. All existing JWTs become invalid — every user must sign in again. Communicate this in advance if planned, or absorb the user-experience hit if reactive.
   - DB password: rotate via the managed Postgres provider, redeploy API + worker with new `DATABASE_URL`.
   - Sentry DSN: rotate in Sentry, redeploy with new value.
3. **Investigate**: pull access logs covering the leak window. Look for unfamiliar IPs, elevated 4xx/5xx, or unusual data egress.
4. **Force re-auth where needed**: if user account data is suspected accessed, set affected `users.is_active = false` and reach out to the user before re-enabling.
5. **Notify**: notify the privacy contact ([PRIVACY CONTACT EMAIL]) within 1 h. UK GDPR Art. 33 may require ICO notification within 72 h if personal data is affected.
6. **Post-incident**: document timeline, root cause, scope, remediation, and corrective actions. File in `docs/30-delivery/incidents/`.

## GDPR / PDPL data subject requests

Customers may request access, correction, deletion, restriction, objection, portability, or withdrawal of consent.

1. Receive request at [PRIVACY CONTACT EMAIL]. Verify the requester's identity (signed-in account confirmation, or government ID for deletion requests).
2. Log the request: requester, date received, type, target user_id.
3. Acknowledge within 5 business days. Substantive response within 30 days (UK GDPR Art. 12).
4. Fulfilment queries (run from a read replica where possible):
   - Account export: `SELECT * FROM users WHERE email = '...'` plus joins for `worker_profiles`, `applications`, `bookings`, `messages`, `ratings`, `notifications`.
   - Deletion: irreversible. Confirm the requester wants legal-hold and audit data removed. Some records (financial, payment) may be retained under separate legal bases — document which.
5. Return data as JSON or CSV. Encrypt the export if delivered by email.
6. Close the ticket, retain the log for at least 2 years.

## Incident Checklist

1. Assign incident owner and note start time.
2. Check API, worker, database, and upload storage health.
3. Decide: rollback, hotfix, or continue monitoring.
4. Preserve logs and error samples before restarting services.
5. Communicate customer impact, workaround, and next update time.
6. After resolution, record root cause, timeline, corrective actions, and owner.

## Routine Operations

- Before client demos: run migrations, seed/demo-data script if needed, check API health, and verify one operator login plus one worker login.
- Before production changes: run backend tests, web `tsc --noEmit`, mobile `tsc --noEmit`, and `docker compose config`.
- Secrets rotation: rotate `JWT_SECRET_KEY` quarterly. All sessions are invalidated on rotation — schedule the change for a low-traffic window and message users. Rotate database credentials through the managed Postgres provider.
