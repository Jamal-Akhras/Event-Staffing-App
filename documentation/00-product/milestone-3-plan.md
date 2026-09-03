# Milestone 3 - Keep the week covered (draft 1)

## Outcome

A worker opens onto the right work for their relationships, records when they can work or are away,
and can request cover or a swap without abandoning a booking. Managers approve time off and shift
changes. An uncovered slot moves through team, pool and market under the venue's explicit settings.
An opted-in worker may automatically accept a shift that the venue offered specifically to them,
using rules that worker authored.

This milestone covers A5, B4, B5, F4, S4, S6, S7, W2, W3, W4 and W6. It also closes the deferred
team-before-pool rung and persists the marketplace choice implied by P3/F1.

## Non-goals

- No rota redesign, multi-seat slot entity or payroll integration. The shift remains atomic.
- No feed ranking, paid placement, applicant ranking or automated rejection.
- No platform-chosen allocation from a pool broadcast. Auto-accept applies only to a named offer.
- No general group chat or standing employment channel. Existing shift/application messaging remains.
- No organisation-wide staff sharing, subscription billing, certification model or availability-based
  wage suggestion.
- No cancellation of an existing booking merely because availability later changes.

## Requirement traceability

| Requirement | Enforcement point | Pinning test |
| --- | --- | --- |
| P3/F1 | Persisted `marketplace_enabled`, set by both registration branches | Join-code, marketplace and migrated-worker registration cases |
| A5/B5/S7/W4 | Availability rules, exceptions and venue-scoped time-off services | Rule precedence, authorization and approval-conflict tables |
| F4/W2 | Server-derived work context and navigator mounted with its resolved initial route | Work-context contract tests plus live team/market/mixed navigation |
| W3 | Confirmed bookings, named offers and open shifts use separate endpoints/actions | Home response tests plus the live worker flow |
| W6 | Venue-scoped batch status evaluator over bookings, time off and availability | Status priority plus cross-venue privacy tests |
| S4 | Typed four-stage venue policy and cumulative audience predicate | Every stage/relationship/status/setting combination at all visibility doors |
| B4/S6 | Booking-scoped change requests and transactional replace/swap allocator | Lifecycle, rollback and PostgreSQL race tests |
| C4 | Availability never filters applications; auto-accept only executes a named worker's rule | Feed/application non-exclusion and pool-broadcast non-allocation tests |
| Feed integrity | Shared access context plus equivalent SQL predicate | Feed, list, detail and application-create matrix |
| X1/X2 | Booking-scoped cover; empty audiences skip or park; no slot entity | Empty venue, multi-seat shift and dropped-booking tests |

## Current seams to preserve

- `BookingAllocator` is the sole capacity, duplicate-booking and overlap authority. PostgreSQL takes a
  worker advisory lock before the shift row lock; in-memory uses one allocator lock.
- `BookingLifecycleService` records booking transitions and restarts the escalation ladder after a
  cancellation or no-show.
- `RotaService` publishes employees directly and leaves named non-employees as private offers. It is
  already 461 lines, so new cover and offer behavior must live in new services rather than expanding it.
- `EscalationService`, `shift_visibility.py`, both worker-feed query repositories, worker shift listing,
  shift detail and application creation collectively enforce private visibility. Every new origin must
  be implemented at every door.
- `worker_relationships` is venue-specific and already supports one worker at several venues.
- The outbox is the durable notification boundary. Scheduled state transitions, such as escalation, scan
  committed rows through the existing worker; auto-accept should follow that durable scan pattern.
- Rota publications and the global event log remain the visible revision and audit records.

## Settled behavior

### 1. Marketplace participation is explicit

Add `worker_profiles.marketplace_enabled`.

- Registration without a join code sets it to `true`.
- Registration through a venue join code sets it to `false`.
- Existing profiles migrate to `true`, preserving the current marketplace.
- A worker may enable or disable it later in Profile settings.
- Disabling it hides unrelated open-market shifts but never hides assigned work, their venue's team
  work, or pool work they are entitled to see.
- Home mode is derived from active relationships plus this flag, never from which screen the client
  last opened.

### 2. Availability is worker intent, not a second booking calendar

Recurring rules say when a worker normally wants work. Dated exceptions say that a particular interval
is available or unavailable. Time off is a venue-specific request for an employed relationship.

- No recurring rules means `availability_configured=false`; existing browsing and manual work continue.
- An unavailable exception wins over an available exception; otherwise an available exception wins
  over the recurring schedule.
- Current status is evaluated for the viewing venue: a live booking anywhere gives `booked`, approved
  time off for that venue gives `away`, then a global unavailable result gives `unavailable`, otherwise
  `available`. Time off from venue A does not tell venue B that the worker is away from all work.
- Pending time off blocks the worker's own auto-accept but does not cancel or hide work.
- Approved time off blocks a new employed rota booking for that venue. Approval returns 409 with the
  conflicting booking IDs until the manager resolves them; it never silently cancels them.
- Recurring availability and exceptions do not filter the feed, reject an application or stop a human
  manager assigning someone. They are displayed as conflicts. This preserves C4.
- Every automated acceptance requires explicitly configured availability and an `available` result for
  the entire shift. Unknown availability fails closed for automation only.

### 3. The home is relationship-aware without duplicating the app

The existing tab set remains stable. `Shifts` is the worker's work home and `Browse` remains discovery.

- A worker with an active permanent, part-time or bank relationship initially opens `Shifts`.
- A worker without employment initially opens `Browse`.
- A worker who is employed and marketplace-enabled has both surfaces; `Shifts` opens first.
- `Shifts` shows confirmed assignments, named offers and time-off state as separate sections, combined
  chronologically across venues with venue and relationship labels plus an optional venue filter.
- `Browse` labels team, pool and open-market items distinctly. Assigned offers do not appear there;
  they appear in `Shifts`.

### 4. The escalation ladder is genuinely assigned -> team -> pool -> market

Add `team` to `SHIFT_ORIGINS` and add a separate `team_hours` control.

- `assigned`: visible only to the named worker.
- `team`: visible to active permanent, part-time and bank workers at that venue.
- `pool`: visible cumulatively to the team and active pool members.
- `market`: remains visible to that venue's team and pool, and additionally becomes visible to unrelated
  workers with `marketplace_enabled=true`. Moving outward never removes an earlier audience.
- `one_off`, ended and invited relationships never create private visibility.
- Each disabled or empty rung is skipped. If no enabled rung has an audience, the slot is parked with
  `needs_attention=true` and the venue is notified.
- Notifications go only to workers newly admitted at a rung; workers who saw the previous rung are not
  notified twice.
- Manual advance may skip outward but may never move a shift inward.

Policy fields are explicit and typed: `named_offer_hours`, `team_hours`, `pool_hours` and
`market_lead_hours`. A null named-offer duration waits for an explicit response; null team or pool skips
that audience; null market prevents automatic publication to unrelated workers. Migration 047 writes a
full policy for existing venues using 12 hours for a named offer, 12 hours for team, the existing
private-window value for pool, and the existing market lead value. The migration freezes those literals
rather than importing application constants.

On entering a rung, compute its exit from that entry time. Named, team and pool windows end after their
configured duration. When the next target is market, publish at the earlier of the current window's end
and `shift.start_time - market_lead_hours`, but never before the current rung began. Recompute after every
drop or manual change rather than carrying stale timestamps.

### 5. A named offer has its own lifecycle

`origin=assigned` plus `assigned_worker_id` is not enough to distinguish pending, declined and expired
offers. Add a `shift_offers` record for non-employed named assignments.

- States: `pending`, `accepted`, `declined`, `withdrawn`, `expired`.
- Sources: `rota`, `cover`, `manual`.
- A shift has at most one pending named offer.
- Accept and decline are authenticated worker actions, idempotent and server-timed.
- Acceptance calls the shared allocator and records a normal confirmed booking plus a booking transition
  with reason `offer_accepted`.
- Decline or expiry closes the offer, clears the assignee and restarts at team, then pool, then market.
- Offer expiry is stamped from the venue's `named_offer_hours`; null means it waits for an explicit
  response or manager action rather than advancing automatically.
- A filled, cancelled, draft, started or reassigned shift cannot accept an old offer.
- The response source is `manual` or `auto`; the resulting booking lifecycle is otherwise identical.

### 6. Cover and swaps do not strand work

Use booking-scoped `shift_change_requests`; do not add slot rows.

- Types: `release`, `cover`, `swap`.
- `release` has one source booking and no replacement. Manager approval cancels it without a reliability
  penalty and restarts the ladder.
- `cover` has a source booking and proposed replacement worker. The replacement accepts first, then the
  manager approves.
- `swap` has two confirmed bookings at the same venue. The other worker accepts first, then the manager
  approves the exchange.
- States: `pending_replacement`, `pending_manager`, `approved`, `declined`, `withdrawn`, `expired`.
- The original booking remains confirmed until final manager approval. A request is not a cancellation.
- Requests expire at the earliest affected shift start and cannot be approved after check-in.
- Replacement workers require an active team or pool relationship with the venue. A one-off worker is
  reached through the normal market ladder instead.
- Approval is one transaction: lock workers in sorted ID order, lock shifts in sorted ID order, recheck
  request/booking/relationship state, booking overlaps and approved time off, cancel old bookings as operator-approved changes,
  allocate replacements, restore published state and mint exactly one rota revision.
- A replacement's explicit acceptance may override their normal recurring availability. Preserve the
  evaluated warning in the request record; only an existing booking or approved time off is a hard block.
- A failed approval changes nothing. Existing bookings survive overlap, capacity and stale-state races.
- Add `cover_approved` and `swap_approved` booking-transition reasons through a frozen migration literal.

### 7. Auto-accept executes a worker decision; it never selects a worker

The C4-safe first version applies only to a named `shift_offer`.

- One rule per worker and venue; only an active pool relationship can enable it.
- Criteria: enabled, accepted role names, minimum hourly rate, minimum notice and maximum booked hours in
  the shift's local week.
- Role matching is trimmed and case-insensitive because roles are currently free text. The weekly cap
  counts live bookings across every venue, using the offered shift's venue-local week.
- A rule matches only when declared availability covers the whole shift, no pending or approved time off
  overlaps, and the shared allocator finds no live overlap.
- The scheduler scans committed pending offers that have an enabled rule, claiming them with
  `FOR UPDATE SKIP LOCKED`; in-memory runs the same service synchronously in tests.
- The job calls the same `ShiftOfferService.accept` used by manual acceptance.
- `auto_accept_attempts` has a unique `offer_id`, the rule version/snapshot, evaluated time, outcome and
  reason. Duplicate delivery replays the stored outcome.
- A mismatch or transient conflict leaves the offer pending for manual action. Full, expired or withdrawn
  offers close normally.
- The worker receives a notification saying the shift was accepted by their rule and can see which rule
  matched.
- Pool broadcasts never invoke auto-accept. Supporting that later would require the platform to choose
  among workers and therefore needs a separate C4/legal decision.

## Data model and migrations

### Migration 046 - worker intent and availability

- Add `worker_profiles.marketplace_enabled BOOLEAN NOT NULL DEFAULT true`.
- Add `worker_availability_rules`: ID, worker FK, IANA timezone, weekday 0-6, local start minute 0-1439,
  duration 1-1440, effective-from date, optional effective-until date, created/updated timestamps.
- Add `worker_availability_exceptions`: ID, worker FK, `available|unavailable`, UTC start/end, optional
  note, created/updated timestamps.
- Add `time_off_requests`: ID, worker, venue FK, UTC start/end, `pending|approved|declined|withdrawn`,
  reason, created/updated, decided-at and decided-by.
- Index rules by worker/effective dates, exceptions by worker/start/end, and time off by venue/status/start
  and worker/start/end.
- Checks enforce ordered intervals, valid weekday/minute/duration, decision metadata only on a decided
  request, and an active interval no longer than 366 days.

### Migration 047 - separate ladder and named offers

- Extend `ck_shifts_origin` with `team`.
- Add `offer_team_at` to shifts; retain `offer_pool_at` and `publish_market_at` for their literal targets.
- Backfill every venue's JSON policy to the complete four-field shape with frozen literals.
- Add `shift_offers`: offer ID, shift and venue FKs, worker ID, source, status,
  offered/expires/responded timestamps and response source.
- Add a PostgreSQL partial unique index for one pending offer per shift; enforce the equivalent in-memory.
- Update the SQLite migration-chain test and prove 045 -> head -> 045 on SQLite and PostgreSQL.

### Migration 048 - cover and swaps

- Add `shift_change_requests` with type, source booking, optional replacement worker and optional second
  booking, venue, status, reason, timestamps and decision actor.
- Add `shift_change_request_transitions` so worker acceptance, manager decisions, withdrawal and expiry
  are append-only and explainable.
- Add partial indexes for a worker's pending requests and a venue's pending-manager queue.
- Widen the booking-transition reason CHECK from a frozen literal for `offer_accepted`, `cover_approved`
  and `swap_approved`.

### Migration 049 - opt-in auto-accept

- Add `worker_auto_accept_rules`: rule ID, worker/venue, enabled, roles JSON, minimum rate, minimum notice,
  maximum weekly hours, version, created/updated timestamps; unique worker plus venue.
- Add `auto_accept_attempts`: attempt ID, unique offer FK, rule ID/version, immutable rule snapshot,
  evaluated-at, outcome and reason.
- Do not put mutable rule criteria on the booking or charge. The attempt is the explanation record; money
  continues to freeze from the booking and relationship at shift start.

All migrations use `batch_alter_table` where needed, contain their own CHECK literals and support both
SQLite and PostgreSQL upgrade/downgrade tests.

## API contracts

### Worker context, availability and home

- `GET /me/relationships`
- `GET /me/work-context`
- `PUT /me/work-preferences` with `marketplace_enabled`
- `GET|PUT /me/availability/rules`
- `GET|POST /me/availability/exceptions`
- `DELETE /me/availability/exceptions/{id}`
- `GET|POST /me/time-off`
- `POST /me/time-off/{id}/withdraw`
- `GET /me/home?starts_from=&starts_before=` with a maximum 62-day range

`/me/home` returns home mode, relationship summaries, current availability, confirmed assignments,
pending named offers and time-off requests. It never embeds the open feed; discovery remains cursor
paginated at `/workers/me/feed`.

### Venue approval and scheduling

- `GET /venues/me/time-off?status=&starts_from=&starts_before=`
- `POST /venues/me/time-off/{id}/approve`
- `POST /venues/me/time-off/{id}/decline`
- Expand `PUT /venues/me` to a typed four-stage escalation policy.
- Expand `POST /shifts/{id}/advance` targets to `team|pool|market` with outward-only validation.

### Offers and shift changes

- `GET /me/shift-offers`
- `POST /me/shift-offers/{id}/accept`
- `POST /me/shift-offers/{id}/decline`
- `GET|POST /me/shift-change-requests`
- `POST /me/shift-change-requests/{id}/accept-replacement`
- `POST /me/shift-change-requests/{id}/decline-replacement`
- `POST /me/shift-change-requests/{id}/withdraw`
- `GET /venues/me/shift-change-requests?status=`
- `POST /venues/me/shift-change-requests/{id}/approve`
- `POST /venues/me/shift-change-requests/{id}/decline`

All mutation endpoints use server time, accept `Idempotency-Key`, replay the original response for the
same key and payload, and return 409 for a stale lifecycle conflict. Foreign venue/worker resources are
returned as 404 where existence would leak.

### Auto-accept

- `GET /me/auto-accept-rules`
- `PUT /me/auto-accept-rules/{venue_id}`
- `DELETE /me/auto-accept-rules/{venue_id}`
- `GET /me/auto-accept-attempts?limit=`

The rule endpoint refuses an ended, invited, employed, one-off or absent relationship. Enabling refuses
until availability is configured. Disabling is immediate and wins if it races an unprocessed offer.

## Implementation phases

Each phase ends with the in-memory and PostgreSQL suites green. Do not defer PostgreSQL behavior until
the end; the critical operations depend on locks, partial indexes and transaction rollback.

### Phase 0 - contracts and shared evaluators

1. Add domain dataclasses and typed schemas in small modules under `models/`, `schemas_workforce.py` or
   new focused schema modules.
2. Add availability/time-off repository protocols and adapters. Later phases add offer, shift-change and
   auto-accept adapters with their own migrations rather than creating unused abstractions up front.
3. Add `AvailabilityService.evaluate_interval` and `current_statuses(venue_id, worker_ids, now)`. Keep
   timezone conversion and rule precedence pure and table-tested, including overnight and DST weeks.
4. Add a batch current-status query for People; do not add one query per directory row.
5. Wire dependencies and repository overrides. Every new provider must appear in
   `apps/api/tests/repository_overrides.py` so the PostgreSQL leg cannot silently receive in-memory data.

### Phase 1 - worker intent, availability and time off

1. Apply migration 046 and update worker profile mappers and every profile-creation path. Password and
   SSO registration without a join code set marketplace true; a join-code registration sets it false.
2. Build worker availability/time-off routes and venue approval routes.
3. Require an active employed relationship for venue-specific time off and scope every manager decision
   to the actor's active venue.
4. On approval, query future live bookings in the interval. Return all conflicting IDs in a 409; write
   no partial decision.
5. Add availability state to directory responses using the batch evaluator and show it in People.
6. Record semantic events for rule replacement, exceptions and every time-off decision.

### Phase 2 - relationship-aware worker home

1. Add `/me/relationships`, `/me/work-context` and bounded `/me/home` composition services.
2. Make the worker feed respect `marketplace_enabled` while retaining assigned/team/pool visibility.
3. Add relationship/audience labels to worker feed responses without introducing ranking.
4. Resolve work context before mounting `BottomTabNavigator`, then choose its immutable initial tab:
   Shifts for employed workers, Browse otherwise. Show a retryable error if context loading fails; do not
   mount Browse as a silent fallback. Never reorder tabs after mount.
5. Refactor `ShiftsScreen` into focused hooks/components for assignments, offers, time off and venue
   filtering. Keep prior attendance, ratings and messaging behavior intact.
6. Add the marketplace toggle under Profile settings and refresh home/feed queries after it changes.

### Phase 3 - team, pool and market as distinct rungs

1. Apply migration 047 and replace `EscalationPolicy` with explicit named-offer, team, pool and market
   fields.
2. Make `next_timestamps` a pure ordered-rung calculation that skips disabled or empty audiences.
3. Update `stamp_new_shift`, `restart_ladder`, sweep and manual advance for `team`.
4. Centralize audience membership in one predicate used by `shift_visibility.py`, in-memory feed and an
   equivalent SQL expression. Keep SQL filtering in the database; do not fetch and post-filter pages.
5. Update Settings to expose separate team and pool windows and accurately display disabled steps.
6. Add matrix tests for every origin x relationship x status x marketplace flag at all four visibility
   doors: cursor feed, worker shift list, detail and application creation.

### Phase 4 - named offers, cover and swaps

1. Apply migration 048, then create `ShiftOfferService`; change rota publish/reassign to create a pending offer for an active
   non-employed assignee rather than relying only on shift fields.
2. Implement manual offer accept/decline. Acceptance uses `BookingAllocator`; decline restarts the full
   ladder. Add expiry to the existing escalation sweep or a focused worker job.
3. Create `ShiftChangeService` and keep it separate from `RotaService`.
4. Extend the allocator with transaction-level replace and swap operations. PostgreSQL locks worker IDs
   then shift IDs in sorted order; in-memory validates the full operation under its allocator lock before
   any write.
5. Manager approval creates one rota revision through an extracted reusable `RotaRevisionService`.
   Move revision minting out of the 461-line `RotaService` when this seam is touched.
6. Extend notification action types and both client routers before emitting a new action. Notifications
   must carry a real offer/request/booking/shift ID that the recipient is authorized to open.
7. Add console queues in Shifts for time off and shift changes, and mobile request/accept/decline flows
   from the affected booking or offer.

### Phase 5 - integrated worker and manager experience

1. Show schedule conflicts while the venue builds or reassigns a rota; approved time off is a hard
   conflict, other declared availability is a visible warning.
2. Show current status and next change in People without exposing availability to unrelated venues.
3. Show assigned, offered and open work with different language and actions. An offer says Accept or
   Decline; an open shift says Apply; a confirmed shift shows attendance and Request cover.
4. Use venue-local dates in the console and each shift's venue timezone in the combined worker home.
5. Add healthy/empty states: all covered, no requests waiting, availability set, and no conflicts.
6. Run a live two-venue flow covering a mixed worker, team-only worker and marketplace-only worker.

### Phase 6 - opt-in named-offer auto-accept (final phase)

1. Apply migration 049 and build rule CRUD plus attempt history.
2. Add `run_auto_accept_sweep` to the existing scheduler. In a bounded loop, select and process one
   committed pending offer per short transaction with `FOR UPDATE SKIP LOCKED`; never hold a batch of
   offer locks while allocating.
3. Implement an idempotent auto-accept handler that reloads the rule, offer, relationship, availability,
   time off, weekly booked hours and shift terms inside one transaction.
4. Call `ShiftOfferService.accept`; do not duplicate allocation, booking-transition, offer-transition or
   notification logic in the worker.
5. Persist every attempt outcome in the same transaction. A repeated sweep reads the unique attempt and
   does nothing.
6. Add the mobile rule editor after the manual offer flow is proven. Explain in plain language that it
   acts only on shifts a venue sends specifically to that worker.
7. Keep pool-broadcast auto-allocation absent and pin that absence with a regression test.

## Verification matrix

### Pure and service tests

- Recurring availability: multiple windows, overnight, DST spring/fall, effective dates and exception
  precedence.
- Current status priority: booked, away, unavailable, available; unconfigured is marked separately.
- Time-off create/withdraw/approve/decline, relationship/status checks and no partial approval on conflict.
- Three-rung timestamp tables across enabled/disabled/empty combinations and late drops.
- Named offer lifecycle, expiry, stale acceptance and retry replay.
- Release, cover and two-booking swap, including replacement decline and request expiry.
- Auto-accept criteria and explicit skip reasons.

### Authorization and visibility tests

- A venue sees availability/status only for workers with a relationship to it.
- A manager cannot decide another venue's time off or shift-change request.
- A worker cannot act on another worker's offer, request, rule or attempt.
- Team-only registration cannot see unrelated market shifts by feed, list, detail or guessed ID.
- Team, pool and market origins match their cumulative audiences in memory and PostgreSQL.
- Draft, parked and assigned-to-someone-else shifts remain invisible.

### PostgreSQL race tests

- Time-off approval versus rota booking: one valid result, never approved leave plus a new booking.
- Offer manual accept versus auto-accept: one booking and one terminal offer response.
- Offer accept versus expiry or reassignment: no stale booking.
- Cover approval versus worker cancellation: either the cover transaction or cancellation wins cleanly.
- Two simultaneous swaps sharing a worker: sorted locks prevent deadlock and only one succeeds.
- Concurrent/repeated auto-accept sweeps: one attempt, one booking, one notification.

### Client and live checks

- Web TypeScript and production build; mobile TypeScript.
- Mobile deep links open an authorized offer/request and recover cleanly when it is stale.
- Live path: join-code worker lands on Shifts, marketplace worker lands on Browse, mixed worker sees both;
  availability and time off update People; approved cover mints one revision; a drop traverses team,
  pool and market; a matching named offer auto-accepts once.
- Full in-memory and PostgreSQL suites, zero unexpected skips, plus migration up/down/up on both engines.

## Ranked risks

1. **C4 boundary.** Pool-broadcast auto-allocation would make the platform choose a winner. The plan avoids
   it by automating only a worker's standing response to an offer already addressed to them.
2. **Atomic swaps.** Two workers and two shifts create deadlock and partial-write risk. Sorted worker then
   shift locks, validate-before-write in memory and PostgreSQL race tests are mandatory.
3. **Visibility drift.** Adding `team` creates another chance for feed/list/detail/application predicates
   to disagree. One domain predicate, an equivalent SQL expression and a full-door matrix pin it.
4. **Timezone errors.** Recurring local rules crossing midnight or DST cannot be compared as naive UTC
   weekdays. Evaluation occurs in the rule timezone and tests both DST boundaries.
5. **Marketplace-mode migration.** Existing workers must remain marketplace-enabled while new join-code
   workers start team-only; registration and migration tests pin both branches.

## Definition of done

- Every listed requirement has an enforcement point and a test, not only a table or screen.
- A worker can be employed at one venue, pooled at another and marketplace-enabled without duplicate data.
- The same worker sees confirmed, offered and open work as distinct states across those venues.
- Availability and time off are visible and audited but never automatically reject an application.
- Release, cover and swap requests retain the old booking until approval and never strand a slot.
- Escalation is assigned, team, pool, market with independent venue controls and private visibility.
- Auto-accept is opt-in, named-offer-only, explainable, idempotent and routed through the shared allocator.
- Both persistence legs, builds, migrations, concurrency tests and the live end-to-end flow are green.

## Suggested commit sequence

1. `Add worker availability and marketplace preferences`
2. `Add the relationship-aware worker home`
3. `Separate team, pool and market escalation`
4. `Add named shift offers and manager-approved cover`
5. `Add worker and manager coverage workflows`
6. `Add opt-in auto-accept for named offers`

Push only after explicit user confirmation.
