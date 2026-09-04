# Milestone 4 — One company, priced properly

Backend-first per D075: clients receive only the minimum functional surface each feature needs to be
exercised and demonstrated; the full visual revamp follows the milestone. Draft 1 was authored by
Fable and adversarially reviewed by Codex against head `f6c0e32`; this final plan incorporates all
fourteen of its deltas. Requirements covered: O1 O2 O3 O5, B2 B5 B7 B8 B9, M1 M2 M3 M5, N2 N5 N6,
I2 I3 I4 I6, L3, L9. Explicitly out: M4 ranked feed (needs L9 history plus the ranking layer),
P9 badges, S9 presentation, payment processing (statements remain the product), AI (its own
session).

## Design principles fixed by review

- **Three concepts, not one, behind O2.** Organisation fee affiliation, cross-site scheduling
  consent, and venue-local audience are modelled separately. A worker employed at a sibling venue
  is *fee-affiliated* (zero-rates the charge) but is never auto-rostered, never PIN-free at the
  other site, and never joins its team rung or feed audience by default.
- **Cross-site scheduling consent is per shift, through the existing named-offer flow.** Assigning
  a sibling-venue employee mints a `shift_offer` the worker accepts or declines, exactly like a
  pool assignment today. No new consent table, no consent invariant broken: acceptance IS the
  consent, recorded per placement. (A standing "work at any site of this group" opt-in is a later
  convenience, not this milestone.)
- **Fee authority is resolved as of shift start, from history.** Commercial agreements are
  effective-dated; the frozen charge carries `fee_basis`
  (venue_employed | organisation_employed | venue_pool | outside), the source venue, and the fee
  schedule that applied — never just a plan name read at approval time.
- **Active venue is session-scoped, not a user-row mutation.** The venue claim lives in the session
  token and is validated against membership on every request; `users.active_venue_id` remains only
  a login default. Switching venue in one tab can never silently repoint another live session.
- **Venue notifications become user deliveries.** Recipient resolution walks memberships;
  deliveries and read receipts are per user. This is a prerequisite for both multi-manager and
  group messaging.
- **Managers are venue-scoped in the database; the permission map lives in code.** Owner and admin
  are org-wide; a manager row carries an explicit venue set. Invitations are persisted, expiring,
  one-use, and grant membership only on acceptance. The last owner cannot be removed.
- **Messages get a real thread model.** `message_threads`, participant intervals
  (joined_at/left_at), `messages.thread_id`, and per-user read receipts. Existing
  application/booking conversations migrate into `direct` threads. A cancelled worker's interval
  closes: history stays readable, new messages stop. Identity in a thread is the sender, not the
  role.
- **Boost rank is part of the ordering tuple and the cursor**, never a post-query splice. The feed
  ordering contract is `relationship_bucket → boost_position (market bucket only) → start_time →
  shift_id`. The commercial promise is "top N of the market section of the feed". Delivered
  positions are recorded on `shift.served` (boost_id, tier, position); the purchase row alone is
  a charge, not proof of delivery.
- **L3 risk information is required for every newly published shift**, plumbed through create,
  update, clone, templates, recurring generation, and every worker acceptance/detail surface.
  The column is nullable only for legacy rows.
- **L9 consent is immutable events** (granted | withdrawn | objected, with purpose, policy version,
  basis, source, timestamp), captured at registration, managed via read *and* write endpoints,
  enforced before any per-worker suggestion logic — which places it ahead of I3.
- **I-figures follow D065**: "filled" means checked in, denominators are exposed, minimum sample
  thresholds return explicit insufficient-data rather than noise. Allocation source is frozen at
  booking time so I6's escalation depth is history, not a read of mutable `shift.origin`.

## Phases

Each phase lands with both suites green (zero PostgreSQL skips), migrations proven up-down-up on
both engines, overrides registered with providers, round-trip tests for every new SQL mapper,
ledger entry, pathspec commit. Seam files have exactly one owner at a time.

### Phase 1 — Tenancy foundations (Fable, migration 052)

- Venue-scoped memberships: `organisation_memberships` gains venue scoping (owner/admin org-wide;
  manager carries an explicit venue set); `manager_invitations` (expiring, one-use, audited,
  membership created on acceptance); role-change endpoint; last-owner guard.
- Session-scoped active venue: venue claim in the session token, validated per request; venue
  switch endpoint reissues the claim; `active_venue_id` demoted to login default.
- `require_permission(actor, permission)` with the role→permission matrix in code; applied to
  billing, plan, settings, venue and manager management. Operational routes stay open to members
  whose scope covers the venue.
- User-level notification deliveries: membership-aware recipient resolution, per-user read
  receipts; existing venue-recipient outbox path migrated.
- Minimal surfaces: venue switcher, manager list/invite/accept, nothing more.

### Phase 2 — Cross-site sharing (Fable, migration 053)

- Organisation staff-discovery endpoint (owner/admin/manager, scope-checked) so sibling employees
  are selectable at all.
- Sibling assignment mints a named offer (consent per shift); acceptance books with `pin`
  attendance at the foreign site.
- `charge_recorder` resolves fee affiliation org-wide as of shift start; charges gain `fee_basis`
  and `source_venue_id`. Bookings freeze `allocation_source` (named | team | pool | market |
  cover | sibling) at allocation — also the substrate for I6.
- O5 rollups through a shared aggregate query layer (one SQL pass per figure, not per-venue
  loops): org billing summary, org insights overview.
- Regressions pinned: O4 (a venueless-team account still posts and fills), D072-style consent (a
  sibling worker is never booked without accepting), feed parity between both query repositories.

### Phase 3 — Commercial model (Fable, migration 054)

- Effective-dated `commercial_agreements` per organisation with `site_entitlements` under them;
  fee schedules (own-pool %, outside %, monthly amount, currency) are immutable rows the agreement
  points at. Enterprise has no seeded price: it exists only through explicit override rows —
  missing configuration can never mean free service.
- Charge freeze resolves plan and relationship as of `booking.start_time` (extending the existing
  transition-replay pattern in `charge_recorder`).
- `commercial_charges` ledger for non-booking lines (kind: subscription | boost), frozen at mint
  with currency, coverage dates, and source schedule id. Monthly subscription minting job (unique
  entitlement+period, scheduler-wired, idempotent re-run test).
- Boost purchasing: `shift_boosts` with tier (top1 | top5 | top10), frozen price, position
  inventory rules (a tier-1 slot is scarce: first purchase wins, conflict returns 409); statement
  line minted at purchase (B8). Composition into the feed is Phase 6.
- Statements gain subscription and boost lines; founding-partner waivers unchanged on top.
- Pricing amounts are data seeded with UNCONFIRMED placeholders (classic 10%/10%, plus £25 per
  site + 0%/10%) pending Q1–Q3.

### Phase 4 — Messaging (Codex, migration 055; starts after Phase 1's notification contract)

- Thread model as fixed above; frozen CHECK swap with per-kind exclusivity (direct ↔
  application/booking, shift_group ↔ shift, employment ↔ relationship); `shift_id` nullable for
  employment threads; indexes and deletion behaviour specified (threads survive shift deletion as
  record — FKs move to SET NULL with retained snapshots of names).
- Group thread per shift (venue side opens first, N3); employment channel per active employed
  relationship, open from either side (N5).
- Export: `GET /venues/me/messages/export?month=` CSV, formula-escaped; retention and
  immutability acceptance tests (N6) — message bodies never mutate, exports are authorized
  per-venue, audit events link thread and message ids.
- Client minimum: the two new thread kinds reachable from existing screens.

### Phase 5 — L3 + L9 (Fable, migration 056)

- `shifts.risk_information` required on every newly published shift; plumbed through create,
  update, clone, templates, recurring generation; surfaced on worker shift detail, offer accept,
  cover ask, application flow. Legacy rows nullable.
- `consent_events` append-only; registration captures terms/privacy acknowledgements (labelled as
  acknowledgements, not consent) and a profiling-consent event kind exists with grant/withdraw
  endpoints and enforcement (no per-worker suggestion runs without a live grant). No backfill:
  existing users are prompted, never assumed.

### Phase 6 — Feed ordering and boost composition (Codex, no migration)

- M5: relationship-bucket ordering (worker's venues → pools → market) inside the SQL ordering
  tuple and the keyset cursor; cursor carries the bucket; parity tests across both repositories;
  cursor stability across bucket boundaries and mid-pagination boost purchases.
- Boost composition: boost position joins the tuple within the market bucket; ≤20% of a page
  boosted with defined rounding for page sizes 1–4; every boosted item labelled (M2); delivered
  position recorded on `shift.served` context (M3 accounting).

### Phase 7 — Insight aggregates (Codex, no migration; after Phases 3 and 5)

- New batched candidate query: workers of the venue's team/pool with role fit, current
  certification, availability over the full interval, no approved time off, no overlapping
  booking. Powers I3; C4-safe (suggestion only, nothing books).
- I2: cost per covered hour by source from frozen charges, with approved-actual vs
  scheduled-forecast separated in the response.
- I3: plan-aware savings (pool cover saves nothing on classic; team availability is the headline).
- I4/I6: fill (= checked in, D065) rates and time-to-fill by lead-time/weekday/relative-pay
  buckets; escalation depth from frozen `allocation_source`; minimum sample thresholds with
  explicit insufficient-data states; org rollups via the shared aggregate layer.
- Console: plain stat rows only (D075), positive-first (D072).

### Close

Docker rebuild; live e2e extending m3: second venue + venue-scoped manager refused at billing;
venue switch in one session leaving another session's scope untouched; sibling employee covering
via an accepted offer at fee_basis organisation_employed and £0 fee; plus-plan statement showing
subscription and boost lines; group thread and employment channel with per-user read state; feed
ordered venues → pools → market with one labelled boost inside the market section; risk information
visible before acceptance; consent grant and withdrawal; the four insight figures over seeded
history with denominators. Acceptance report; nothing pushed without confirmation.

## Migrations

052 tenancy (Fable) → 053 cross-site + allocation source (Fable) → 054 commercial (Fable) →
055 messaging (Codex) → 056 consent + risk (Fable). Numeric order is landing order; every
migration is unconditional (the schema guard expects one deterministic head).

## Open decisions (user)

- **Q-A (blocks Phase 3 minting only):** the subscription unit. Recommended per D071: per site —
  entitlements make the answer data either way.
- **Q-B:** confirm cross-site scheduling as per-shift offers (recommended) vs a standing
  work-anywhere opt-in.
- **Q-C:** placeholder prices (classic 10%, plus £25/site + 0%/10%, enterprise explicit-only)
  acceptable until Q1–Q3 are settled.
- **Q-D:** boost promise wording "top N of the market section" and the 20% page cap.

## Deferred, recorded

Org-wide team escalation rung; standing cross-site opt-in; venue-custom roles (permission
catalogue in DB); M4 ranked feed; proration/cancellation flows beyond period boundaries; badges
P9; S9.
