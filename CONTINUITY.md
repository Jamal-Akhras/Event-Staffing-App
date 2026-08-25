# Continuity Ledger

## Snapshot
- 2026-08-19 [USER] Goal: launch a hospitality shift marketplace first, then expand into adjacent local-service categories.
- 2026-08-19 [USER] Vision: feed-based discovery, mutual trust/reviews, flexible work, broad task categories, marketplace payments, subscriptions, and promoted listings.
- 2026-08-19 [CODE] Current product is a strong venue/event-staffing MVP with web operator and mobile worker surfaces.
- 2026-08-19 [CODE] Core lifecycle exists: auth, profiles, shifts, applications, approval, bookings, attendance, messaging, reliability, notifications, ratings, maps, and earnings views.
- 2026-08-24 [CODE] Processor money movement remains deferred; direct venue-payment attestations and bilateral worker/venue reputation are implemented.
- 2026-08-19 [CODE] User roles are fixed as worker or operator, and listings are venue-oriented shifts with free-text role/location.
- 2026-08-19 [ASSUMPTION] Product-readiness estimate: ~70% of a demonstrable event-staffing MVP, ~50-55% of a launchable narrow marketplace, ~30-35% of the broad final vision.
- 2026-08-19 [USER] Hospitality/events is confirmed as the initial beachhead; broader categories come after the first market works.
- 2026-08-19 [USER] Bath is the likely initial launch city, pending final confirmation.
- 2026-08-19 [MILESTONE] Blank two-account partner demo prepared and verified live end-to-end (`venue@temp.com` / `user@temp.com`, schema 019, all marketplace tables empty).
- 2026-08-20 [USER] Clarified that a founding-venue “free” offer must still fund worker wages; only the platform/service fee is proposed to be waived.
- 2026-08-20 [TOOL] Indeed Flex is a direct UK hospitality competitor with shift posting, verified workers, timesheets, ratings, talent pools, payroll-related services, and a published 15% wage markup.
- 2026-08-20 [USER] Long-term ambition includes becoming a major competitor to national flexible-staffing platforms such as Indeed Flex.
- 2026-08-26 [CODE] Organisation/venue ownership and a reusable environment-level operator invite gate exist, but there is no persisted partner-code redemption, billing plan/trial/entitlement, fee enforcement, or account UI status.
- 2026-08-24 [CODE] The unmounted quote-only processor prototype is not part of the launch contract; current bookings record externally paid wages with authenticated audit fields.
- 2026-08-20 [USER] Considering an employer-paid platform business model while venues employ and pay workers directly.
- 2026-08-21 [USER] Before further app work, create a cofounder-facing document covering the product thesis, Indeed Flex analysis, differentiated offer and commercial model; plan the document before drafting.
- 2026-08-24 [CODE] Durable uploads, account privacy, geocoding persistence and release operations are implemented; public launch still needs legal/classification decisions, production accounts/credentials and final UI QA.
- 2026-08-21 [CODE] The existing React/Vite + Expo/React Native + FastAPI/Postgres/Redis modular-monolith stack is appropriate for the Bath pilot and foreseeable growth; production architecture needs hardening, not a rewrite.
- 2026-08-21 [USER] Scalability, database management, a public acquisition website and convenient identity-provider sign-in are now explicit product-readiness concerns.
- 2026-08-24 [CODE] Worker discovery now uses a market-scoped, indexed PostgreSQL feed with server-side timing/pay/search filters and opaque cursor pagination; legacy list endpoints retain bounded result windows.
- 2026-08-21 [USER] Scalable-foundation plan finalized after a code-verified review; revised Phase 0-7 sequence approved with first slice Phase 0 + Phase 1 (see D022, D025-D028).
- 2026-08-22 [CODE] Scalable-foundation Phases 0-4 are complete: PostgreSQL-backed transactions/integrity, organisation/venue isolation, normalized markets/feed queries, and stateless S3-compatible uploads are green.
- 2026-08-22 [CODE] Public acquisition pages use a premium cream/navy/green system with restrained kinetic product motion; employer operations remain under protected `/app` routes.
- 2026-08-24 [CODE] Backend/API launch hardening and a local red-team pass are complete through migration 029; uploads are now Pillow-decoded and re-encoded, so only the Expo 57 migration remains explicitly deferred.

## Decisions
- 2026-08-19 D001 ACTIVE [ASSUMPTION] Evaluate the app as a two-sided services marketplace, not only an event-staffing tool.
- 2026-08-19 D002 PROPOSED [ASSUMPTION] Preserve the booking state machine and modular backend; evolve the surrounding user, listing, trust, and payment models instead of rewriting.
- 2026-08-19 D003 ACTIVE [USER] Launch scope is hospitality staffing; expansion is deferred until the narrow marketplace is working.
- 2026-08-19 D004 PROPOSED [USER] Use Bath as the pilot city.
- 2026-08-19 D005 SUPERSEDED [USER] A polished seeded sales demo is not required; use the session as a transparent product review with a prospective partner.
- 2026-08-19 D006 ACTIVE [USER] Use two temporary login accounts and no seeded marketplace records for the partner walkthrough.
- 2026-08-20 D007 PROPOSED [ASSUMPTION] Compete initially through Bath-specific hospitality density, independent-venue service, bilateral trust, and worker protections rather than national breadth.
- 2026-08-20 D008 PROPOSED [ASSUMPTION] Treat direct hiring as a supported conversion path with an employer-paid transfer option, not as worker misconduct or a problem solved solely by hiding contact details.
- 2026-08-20 D009 PROPOSED [ASSUMPTION] Pursue scale through a repeatable city-by-city hospitality liquidity playbook before expanding categories or competing nationally.
- 2026-08-20 D010 PROPOSED [ASSUMPTION] Offer the first ten Bath venues a capped founding-partner trial (time and completed-shift limits), with the normal future fee disclosed from day one, rather than a blanket free year.
- 2026-08-20 D011 PROPOSED [ASSUMPTION] Administer the first-ten-venue offer manually before building automated billing; add server-controlled trial automation only after real usage validates the rules.
- 2026-08-20 D013 PROPOSED [ASSUMPTION] Under a direct-venue-pay model, keep work-finding free for workers and charge venues separately through completed-booking fees, subscriptions, and optional urgent-listing upgrades.
- 2026-08-20 D014 PROPOSED [ASSUMPTION] Differentiate as Bath's hospitality relationship network: transparent venue quality, repeat local teams, fair matching, direct progression and no punitive lock-in, rather than a smaller general-purpose temp agency.
- 2026-08-20 D015 PROPOSED [ASSUMPTION] Do not treat app-based booking, generic mutual ratings, verification, messaging, favourites or rapid matching as defensible differentiators because Indeed Flex already offers them.
- 2026-08-21 D016 PROPOSED [ASSUMPTION] Use a concise internal strategy-and-decision memo for cofounder alignment, with evidence, explicit hypotheses, trade-offs and decisions required rather than investor-style sales language.
- 2026-08-21 D017 ACTIVE [USER] Keep the modular monolith and managed PostgreSQL; scale through stateless API replicas, object storage, durable jobs, query/index improvements and observability before service decomposition.
- 2026-08-21 D018 PROPOSED [ASSUMPTION] Add public worker and employer acquisition routes to the existing web app for launch, with the employer dashboard under a protected `/app` route; defer a separate SEO framework until content acquisition warrants it.
- 2026-08-21 D019 SUPERSEDED [ASSUMPTION] Original scalable-foundation sequence omitted an effective PostgreSQL test-harness prerequisite and bundled the venue split with mechanical schema corrections.
- 2026-08-21 D020 ACTIVE [USER] Introduce an organisation/venue separation and memberships before accumulating real customer data: one organisation may own multiple isolated venues, while separate registrations remain separate organisations.
- 2026-08-21 D021 PROPOSED [ASSUMPTION] Use a transactional database outbox for guaranteed email/push/domain events; select any external queue library only after the user confirms the dependency choice.
- 2026-08-21 D022 ACTIVE [USER] Revised sequence: effective PostgreSQL integration harness; transactional integrity; mechanical time/money/deletion corrections; separate organisation/venue migration; query/geo work; storage; at-least-once outbox/jobs; operations; load validation.
- 2026-08-21 D023 SUPERSEDED [USER] Phase 0 ownership ended when Fable 5 completed it; Codex's subsequent Phase 1 backend write-path reservation is also released now that Phase 1 is complete.
- 2026-08-21 D024 ACTIVE [USER] Public acquisition website and `/app` dashboard separation are implemented entirely within `apps/web`; marketing copy remains provisional by design.
- 2026-08-20 D012 PROPOSED [ASSUMPTION] Describe the founding offer as “no platform fee”; venues still fund wages and all applicable statutory employment costs unless an explicit subsidy is budgeted.
- 2026-08-21 D025 ACTIVE [USER] Approved first implementation slice: Phase 0 (genuine PostgreSQL CI/test harness) then Phase 1 (shared request-scoped sessions, atomic transaction boundaries). Phase 1 email delivery stays best-effort-after-commit until the Phase 5 outbox; scheduler/worker jobs get a fresh session per invocation.
- 2026-08-21 D026 ACTIVE [USER] Launch-phase geo access path: normalized city/market id on venues, venues-by-city index, partial index on open shifts by venue and start time; exact distance only after candidate narrowing; PostGIS+GiST when cross-city radius search matters; no four-column geo B-tree.
- 2026-08-21 D027 ACTIVE [USER] In-memory repositories are demoted to lightweight unit-test fakes; endpoint, transaction, ownership and concurrency tests run against PostgreSQL; no parity promise between persistence implementations.
- 2026-08-21 D028 ACTIVE [USER] Revised estimates: Phase 0 1-2d, Phase 1 5-7d, 2A 4-6d, 2B 4-6d, remainder ~16-26d; full foundation 6-9 focused weeks; Bath-pilot minimum ~4-5 weeks.
- 2026-08-21 D029 ACTIVE [USER] Multi-venue delivery is deliberately phased: keep the current single-venue demo, complete Phase 1 transactions, then add the organisation/venue schema with registration creating one organisation plus one venue; defer invitations, roll-up analytics and organisation billing until demanded.
- 2026-08-21 D030 ACTIVE [USER] Phase 2A deletion policy preserves durable marketplace history: physical shift deletion is restricted once applications or bookings exist, notifications survive with a cleared shift reference, and ephemeral feed state may cascade.
- 2026-08-22 D031 ACTIVE [CODE] PostgreSQL now uses canonical organisations, venues, memberships, active_venue_id and venue_id; account_id plus /accounts/me remain temporary compatibility aliases for existing clients and demo flows.
- 2026-08-22 D032 ACTIVE [USER] Phase 3 runs in parallel with disjoint ownership: Codex owns `apps/api` migration/query/API/tests; Fable owns `apps/web` and `apps/mobile` market/feed clients against the locked contract, with no shared-file edits or commits.
- 2026-08-22 D033 ACTIVE [USER] Do not introduce Kafka or Kubernetes now; reconsider Kafka when durable replay/multiple independent event consumers are required and Kubernetes when the service fleet or platform constraints justify cluster operations.
- 2026-08-22 D034 PROPOSED [ASSUMPTION] Use the provider-portable `boto3` S3 API adapter, with Cloudflare R2 recommended for the first production bucket; local filesystem storage is development-only.
- 2026-08-23 D035 ACTIVE [USER] Model the initial launch as founder-built and partner-marketed with no employees, founder salaries or assumed paid acquisition/events; cash planning should focus on hosting, distribution, company setup and essential compliance.
- 2026-08-23 D036 ACTIVE [USER] Ratings use an Uber-style automatic post-shift star prompt on worker mobile and venue web; dismissal is temporary and an unrated completed shift may prompt again later.
- 2026-08-23 D037 ACTIVE [USER] Operational recovery is explicit and audited: close preserves bookings while rejecting pending applications; whole-shift and individual booking cancellation require reasons and authenticated actors; worker withdrawals retain history; pre-booking edits are broad, while booked contractual terms are locked.
- 2026-08-23 D038 ACTIVE [USER] Phase 5 outbox runs as two disjoint parallel streams: Codex owns `apps/api/**`, domain, migrations, worker/deployment and backend tests; Fable owns only `apps/web/**` and `apps/mobile/**` against the locked actor-scoped notification contract. Native Expo push dependency awaits explicit approval.
- 2026-08-23 D039 ACTIVE [CODE] Phase 5 uses PostgreSQL as the durable queue: short `SKIP LOCKED` claims, five-minute recoverable leases, exponential retries, eight-attempt dead letters and idempotent in-app materialization; SMTP remains at-least-once without provider idempotency.
- 2026-08-24 D040 ACTIVE [USER] Native push dependencies are approved: use SDK-54-compatible `expo-notifications`, `expo-device` and `expo-constants`; request permission contextually from notification settings and use a development/release build rather than Android Expo Go.
- 2026-08-24 D041 ACTIVE [USER] Complete backend/API/security launch hardening, then red-team the owned local app and patch exploitable findings before UI polish.
- 2026-08-24 D042 ACTIVE [CODE] Venue-paid wages are represented as explicit external-payment attestations with method, reference and authenticated recorder; no processor money movement is implied.
- 2026-08-24 D043 ACTIVE [CODE] Production disables API documentation, fails closed on unsafe DB/CORS/email/storage configuration, checks schema/readiness, and serves transport/browser security headers.
- 2026-08-24 D044 SUPERSEDED [ASSUMPTION] Decode/re-encode uploads with Pillow only after explicit dependency approval; upgrade Expo SDK 54 to 57 as a separately planned breaking migration, not an audit-force side effect.
- 2026-08-25 D046 ACTIVE [CODE] A message thread is one conversation per worker per shift: an application and the booking it produces resolve to the same thread, every message stores both ids, and operator access is venue-scoped (`shift.account_id == actor.account_id`, falling back to `operator_id` for legacy shifts) to match the shift routes.
- 2026-08-24 D045 ACTIVE [USER] Pillow (`pillow==12.3.0`) is approved: every upload is decoded, header-checked against a 40M-pixel ceiling before decode, EXIF-orientation-corrected, downscaled to a 2048px edge, stripped of metadata and re-encoded in its source format (JPEG/PNG/WebP); the Expo 57 migration stays a separately planned breaking change.
- 2026-08-26 D046 ACTIVE [USER] Defer the founding-partner feature for a later build. Keep it separate from `OPERATOR_INVITE_CODES`; use auditable, rate-limited partner codes that grant organisation-scoped entitlements with expiry/redemption limits and dashboard status. Begin with a secure management command until a staff admin plane exists; fix case-insensitive PostgreSQL email identity before public signup, and treat automatic fee enforcement as a separate billing slice.
- 2026-08-26 D047 ACTIVE [USER] Use one canonical whole-app documentation library for founders and engineers; do not maintain separate cofounder and technical versions. Split by subject for maintainability, but explain jargon, consequences, trade-offs and open decisions in the same documents so non-technical review informs product decisions.

## Done (recent)
- 2026-08-26 [CODE] Canonical whole-app documentation library completed under `documentation/`: 23 linked Markdown files cover product, decisions, architecture, clients, domains, database, APIs, flows, operations, testing/readiness, future designs and visual-asset governance with 42 Mermaid diagrams.
- 2026-08-24 [CODE] Upload re-encoding slice completed: `services/image_processing.py` (Pillow) sits behind `read_processed_image`; the three upload routes store only re-encoded bytes with server-derived extension/content type; endpoint tests use real generated images.
- 2026-08-24 [CODE] Security/privacy/API slice completed: migrations 026-029 add session revocation, account anonymisation/reporting, direct-payment audit and idempotency; stable errors, bounded inputs, actor rate limits and verified mutations ship.
- 2026-08-24 [CODE] Operations slice completed: real readiness, worker heartbeat/outbox health, schema guard, request IDs/security headers, production config fail-closed behavior, pre-deploy migrations, dependency gates and exact Python pins.
- 2026-08-23 [CODE] First security/recovery slice completed: rating identity/eligibility/venue ownership are enforced, pending prompts are personalised, automatic post-shift modals ship on both clients, and unsafe direct booking creation is no longer public.
- 2026-08-25 [CODE] Messaging ironed out: application/booking threads unified (they had split after approval so venue and worker talked past each other), venue-scoped operator access, uuid message ids (timestamp ids could collide), blank messages rejected, `POST /shifts/{id}/messages/read` marks the other side's messages read and both clients call it, push preview truncated to 140 chars, validation handler now encodes pydantic errors (custom validators 500'd before).
- 2026-08-22 [CODE] Phase 4 completed: provider-portable S3 storage plus local dev adapter, production fail-fast configuration, transaction-aware object cleanup, venue-photo retirement, safer content/extension validation, live upload route-order repair, and absolute-CDN client compatibility.
- 2026-08-23 [CODE] Operational recovery slice completed: venue shift edit/close/cancel and individual booking cancellation, worker application withdrawal/booking cancellation, audit fields, atomic notifications and explicit confirmation UX ship across API/web/mobile.
- 2026-08-24 [CODE] Notification improvements completed: inbox and system taps target exact shifts/applications/bookings/messages; native permission, Expo token registration/refresh, foreground handling and logout revocation are wired.

## Now
- 2026-08-26 [TOOL] `main` is synchronized with `origin/main` at `39cf8fb`; review of incoming range `0bd6875..39cf8fb` found no actionable defects.
- 2026-08-25 [CODE] Web UI direction canvas (A Command desk / B Concierge / C Week board; Overview + Post-a-shift each) is published for review; B Concierge also published as a public-shareable static page. Direction not yet chosen.
- 2026-08-25 [CODE] Messaging changes are verified in-memory only (174 passed); the PostgreSQL leg has not been re-run on this PC. Open policy question: whether sending stays allowed on cancelled shifts / withdrawn applications (reading is unaffected).
- 2026-08-23 [CODE] Migration 023 adds immutable rater identity and valid-role enforcement; existing ratings backfill identity from their booking participant.
- 2026-08-24 [CODE] Account deletion/export, reporting/disputes, worker-facing venue reputation, production observability, session revocation, stable errors, bounded inputs and mutation rate limits are implemented.
- 2026-08-24 [CODE] Red-team findings patched: cross-venue object deletion confused-deputy, direct avatar URL injection, encoded storage traversal, JWT claim escalation tests, and geocoding-before-commit ordering.
- 2026-08-23 [CODE] Bath is reference market `bath-gb`; the local PostgreSQL verification server is stopped.
- 2026-08-24 [TOOL] Final backend verification: in-memory 160 passed + 44 PostgreSQL skips; PostgreSQL 204 passed with zero skips; full PostgreSQL base-to-029 rebuild passed.

## Next
- 2026-08-26 [USER] Later founding-partner slice: add partner-code and organisation-entitlement persistence, atomic owner redemption, account/dashboard status, audit fields and PostgreSQL concurrency/isolation tests; preserve manual grants and defer invoice calculation to the billing engine.
- 2026-08-24 [ASSUMPTION] Proceed to UI polish while preserving the now-frozen auth/privacy/report/reputation/direct-payment/error/upload contracts; merge Dependabot patch/minor bumps only after CI is green.
- 2026-08-24 [ASSUMPTION] Two deferred dependency slices: the Expo SDK 57 migration (carries react-native, react, screens, safe-area-context, expo-status-bar) and a web toolchain slice (React 19, Vite 8, plugin-react 6, TypeScript 7); bcrypt stays at 4.0.1 until passlib is replaced.
- 2026-08-24 [ASSUMPTION] Phase 7 load validation and a planned Expo SDK 57 migration follow against the release candidate; production EAS credentials remain external setup.
- 2026-08-21 [ASSUMPTION] Web stream: finalise brand and marketing copy, then connect real store/waitlist destinations when distribution details exist.

## Open questions
- 2026-08-26 [USER] UNCONFIRMED: founding-partner offer duration, completed-shift cap, redemption limit, whether it covers every venue in the organisation, and the standard fee displayed alongside the waiver.
- 2026-08-19 [USER] UNCONFIRMED: final confirmation of Bath and the legal entity/jurisdiction.
- 2026-08-19 [USER] UNCONFIRMED: initial hospitality roles and venue types.
- 2026-08-19 [USER] UNCONFIRMED: which product decisions the prospective partner should help shape during the walkthrough.
- 2026-08-20 [USER] UNCONFIRMED: whether the launch company will act as an employment business, employment agency, or a narrower software marketplace.
- 2026-08-20 [ASSUMPTION] UNCONFIRMED: preferred employer transfer-fee/extended-hire policy for direct worker conversion.
- 2026-08-20 [USER] UNCONFIRMED: eventual standard employer fee and which employment/payroll costs remain pass-through during launch incentives.
- 2026-08-21 [USER] UNCONFIRMED: whether the immediate distribution target is a private hosted demo, TestFlight/internal beta, or public App Store and Play Store launch.
- 2026-08-21 [USER] UNCONFIRMED: final brand/app name, legal entity, support/privacy contacts and production hosting accounts.
- 2026-08-21 [USER] UNCONFIRMED: whether workers may also register/use core flows on the web or are intentionally mobile-only.
- 2026-08-21 [ASSUMPTION] UNCONFIRMED: custom OIDC implementation versus a managed authentication provider for Google and Apple sign-in.
- 2026-08-22 [ASSUMPTION] UNCONFIRMED: final production object-storage provider/bucket and explicit confirmation of the `boto3` adapter (Cloudflare R2 recommended).
- 2026-08-24 [USER] UNCONFIRMED: Expo/EAS project ID plus iOS APNs and Android FCM credentials; native registration code is ready but remote delivery requires these external credentials and a development/release build.

## Working set
- 2026-08-26 [CODE] `documentation/{README.md,00-product,10-architecture,20-domain,30-data,40-api,50-flows,60-operations,70-quality,80-future}/`, `CONTINUITY.md`
- 2026-08-26 [CODE] `apps/api/src/{routes/auth,routes/tenancy,services/operator_invites,auth/dependencies}.py`, `apps/api/src/db/tenancy_models.py`
- 2026-08-24 [CODE] `apps/api/alembic/versions/{026_auth_session_version,027_account_privacy_and_reports,028_direct_payment_attestation,029_idempotency_records}.py`
- 2026-08-24 [CODE] `apps/api/src/routes/{auth_account,reports,ratings,payments,shifts,accounts,uploads}.py`
- 2026-08-25 [CODE] `apps/api/src/services/message_service.py`, `apps/api/src/routes/messages.py`, `apps/api/src/api_errors.py`, `apps/api/tests/test_message_threads.py`, `apps/{web,mobile}/src/components/MessageThread.tsx`
- 2026-08-24 [CODE] `apps/api/src/services/{image_processing,upload_validation,account_privacy,idempotency,health,stored_upload}.py`
- 2026-08-24 [CODE] `apps/api/src/{api_errors,request_middleware,config,rate_limit}.py`
- 2026-08-24 [CODE] `apps/api/src/db/{schema_guard,trust_models,idempotency_models}.py`
- 2026-08-24 [CODE] `apps/api/tests/{test_image_processing,test_upload_endpoints,test_red_team_security,test_postgres_security_hardening,test_health_and_errors,test_idempotency}.py`
- 2026-08-24 [CODE] `.github/workflows/ci.yml`, `.github/dependabot.yml`, `render.yaml`, `requirements.txt`
- 2026-08-24 [CODE] `apps/web/package.json`, `apps/web/package-lock.json`, `apps/mobile/package-lock.json`

## Receipts
- 2026-08-26 [TOOL] Documentation validation: 23 Markdown files, 2,391 lines and 42 Mermaid diagrams; all local Markdown links resolve, all diagram blocks use supported starts, code fences are balanced, sensitive-email/stale-encoding scan is empty and `git diff --check` reports no whitespace errors (only pre-existing generated-context CRLF notices). Browser-local capture failed and two privacy-redaction image generations altered unrelated UI text, so no misleading or personal-data screenshot was admitted; the docs include a demo-capture catalogue instead.
- 2026-08-26 [CODE] Founding-partner/account audit: `OPERATOR_INVITE_CODES` is a reusable comma-separated environment allow-list used only before operator registration; it has no expiry, redemption limit, audit record, organisation link, entitlement, or UI. Registration atomically creates one organisation, venue, owner membership, user, and verification outbox event; PostgreSQL tests cover rollback and cross-organisation isolation. Production gaps include case-sensitive SQL email identity despite case-insensitive in-memory behavior, no membership-management/active-venue-switching API, no staff admin plane, and no commercial entitlement/billing model.
- 2026-08-26 [TOOL] Pull/review verification: exact Python pins passed `pip check` and 168 in-memory tests with 44 PostgreSQL-only skips; Pillow upload tests passed 15/15; exact web Sentry 10.70.0 production build passed (481 modules, 336.04 kB); exact mobile Reanimated 4.1.7 TypeScript and Expo SDK checks passed; `git diff --check` clean. PostgreSQL was not rerun because the incoming range has no schema change; FastAPI 0.141.1/Starlette 1.6.0 emits a non-blocking TestClient `httpx` deprecation warning.
- 2026-08-25 [TOOL] Messaging verification: in-memory suite 174 passed + 44 PostgreSQL skips (6 new thread tests: application/booking continuity, venue colleague access vs other venue 403, thread-read marks only the other side, blank/trimmed content, distinct ids under rapid sends, sender cannot self-mark read); web and mobile `tsc --noEmit` clean; all touched files ≤300 lines.
- 2026-08-24 [TOOL] Dependabot triage: 26 PRs (three waves) reviewed against CI and Expo SDK 54 `bundledNativeModules.json`; 11 bumps landed on `main` (uvicorn 0.52.4, alembic 1.19.1, pytest 9.1.1, boto3 1.43.77, sqlalchemy 2.0.52, pydantic 2.13.4, python-multipart 0.0.32, python-dotenv 1.2.3, fastapi 0.141.1, @sentry/react 10.70.0, react-native-reanimated 4.1.7), 15 closed; the full pinned set passed 168 in-memory tests together locally; `.github/dependabot.yml` ignore rules now exclude Expo-pinned packages, web-toolchain majors, bcrypt and Docker Python; `gh` CLI 2.98.0 installed and authenticated on this PC.
- 2026-08-24 [TOOL] Pillow slice verification on the second PC (miniconda Python 3.13): in-memory suite 168 passed + 44 PostgreSQL skips; 7 new image-processing tests cover EXIF stripping, PNG alpha/text-chunk removal, WebP round-trip, 2048px downscale, garbage-after-magic rejection, decompression-bomb header rejection and unsupported-format rejection; PostgreSQL leg not re-run (no schema change). A stray untracked `apps/api/nul` file that broke `update-context.ps1` was deleted.
- 2026-08-24 [USER] Repository-wide handoff requested: commit all legitimate source, client, migration, tests, deployment, documentation and generated context changes for continuation on another PC; exclude machine-only caches and secrets.
- 2026-08-24 [TOOL] Final database verification: 204 tests passed with zero skips on PostgreSQL; 160 passed with 44 PostgreSQL-only skips in-memory; PostgreSQL fully downgraded to base and rebuilt through 029.
- 2026-08-24 [TOOL] Red-team regression coverage proves signed JWT tampering/claim escalation rejection, production dev-header rejection, verified mutation gates, deletion confirmation/session revocation, cross-tenant report isolation, idempotency races and media ownership isolation.
- 2026-08-24 [TOOL] Client/dependency verification: web production build passed (451 modules, 335.86 kB), web production audit reports zero vulnerabilities, mobile TypeScript and Expo SDK-54 package checks pass; mobile retains 10 high/8 moderate Expo-toolchain findings whose complete fix requires Expo 57.
- 2026-08-24 [TOOL] Render Blueprint YAML parses with four services; official Render documentation confirms `preDeployCommand`, static-site headers and forwarded client-IP behavior; Docker cannot be built locally because Docker is not installed.
- 2026-08-24 [TOOL] Backend/security/API audit confirmed strong PostgreSQL transactions, ownership checks, Redis-backed production rate limiting, object storage and outbox foundations; CI lacks dependency/container security checks, `/health` is shallow, production DB/CORS startup validation is incomplete, and background geocoding has no persisted-coordinate test.
- 2026-08-23 [TOOL] Phase 5 backend final verification: PostgreSQL migrations fully downgraded to base and rebuilt through 025, then 173 tests passed with zero skips; concurrency tests proved producer idempotency, `SKIP LOCKED` dispatch and stale-lease recovery; local server stopped.
- 2026-08-23 [TOOL] Phase 5 lightweight verification: 135 tests passed with 38 PostgreSQL skips; SQLite migration upgrade/downgrade, Python compileall and backend diff check passed; all touched code files remain below 300 lines.
- 2026-08-23 [TOOL] Rating/security final verification: PostgreSQL rebuilt migrations 001-023 and passed 155 tests; in-memory leg passed 125 with 30 PostgreSQL skips; focused SQLite upgrade/downgrade passed 3 tests.
- 2026-08-23 [TOOL] Client verification: web production build passed (442 modules, 319.49 kB JS), mobile TypeScript and Python compileall passed, diff check was clean, all touched code files remain below 300 lines, and the local PostgreSQL server was stopped.
- 2026-08-23 [TOOL] Operational recovery verification: PostgreSQL migrations rebuilt 001-024 and 024 reversed to 023 and reapplied; full PostgreSQL leg passed 163 tests including persisted audit and rollback-on-notification-failure coverage; in-memory/domain passed 130 with 33 PostgreSQL skips; SQLite migration suite passed 3.
- 2026-08-23 [TOOL] Recovery client verification: web production build passed (446 modules, 326.99 kB JS), mobile TypeScript and Python compileall passed, diff check was clean, all touched code files remain below 300 lines, and the local PostgreSQL server was stopped.
- 2026-08-22 [TOOL] Phase 2B migration verification passed SQLite legacy backfill/downgrade, PostgreSQL 021-to-020-to-021, and a complete PostgreSQL base-to-head rebuild through revision 021.
- 2026-08-22 [TOOL] Phase 2B final verification: PostgreSQL 129 passed, in-memory 90 passed + 20 PostgreSQL skips, web production build 435 modules, mobile TypeScript clean; all touched code modules are below 300 lines.
