# UI Revamp — Information Architecture (draft 1)

The backend now supports the full feature set (M1–M5). This plan fixes **where every capability
lives** — the tabs, the destinations, and what sits under each — before any visual work. It does
not decide look-and-feel (palette, type, motion); that is a separate craft pass. It builds on the
established language: D069 (worker app inherits the console's visual language; accent once per
screen; status is a word + small mark), D070 (worker settings are a drilled list, not tabs), D071
(management tool: permanent + pool + temp in one place; wages never through the app), D072
(positive-first, screens double as sales material).

## The problem the revamp solves

The current IA was designed for the MVP (post a shift → applications → bookings). Since then the
backend grew a whole operating loop that has **no clear home** in either client:

- **Worker:** availability rules + exceptions + time off, venue relationships, named shift offers
  (accept/decline + auto-accept rules), release/cover change requests, certifications, profiling
  consent, feed appeals, direct messages.
- **Operator:** availability/time-off approval, the four-field escalation policy, named-offer and
  cover/release queues, certification requirements, org membership + invitations + venue switching,
  billing plans/subscription/boosts, direct messages, feed-appeal review, the assistant.

Today these are reachable only through ad-hoc links or not at all. The revamp gives each a home and
a predictable place to look.

## Capability inventory (every backend surface needs a home)

Grounded in `apps/api/src/routes/`. Each row must land somewhere in the IA below.

| Capability | Routes | Worker home | Operator home |
|---|---|---|---|
| Marketplace feed (ranked, M5) | `worker_feed` | Browse | — |
| Bookings / the week | `bookings`, `shifts` | Shifts | Schedule |
| Applications | `applications` | Applications | Requests |
| Named offers + auto-accept | `shift_offers`, `auto_accept` | Shifts → Offers | Schedule (queue) |
| Release / cover requests | `shift_changes` | Shifts → (contextual) | Requests |
| Availability + time off | `worker_availability`, `worker_time_off`, `availability_views`, `venue_time_off` | Profile → Availability | Requests (approvals) |
| Certifications | `worker_certifications` | Profile → Certifications | People / shift form |
| Relationships (my venues) | (workers/relationships) | Profile → My venues | People |
| Earnings / statements | `bookings`, `commercial` | Earnings | Billing |
| Messages (threads) | `messages` | Messages (header) | Messages (header) |
| Consent (profiling) | `consent` | Profile → Privacy | Settings → Privacy |
| Feed appeals | `feed_appeals` | Browse (contextual) | Requests (system review) |
| Rota builder + templates | `shifts`, `templates` | — | Schedule |
| Insight | `insights`, `insight_aggregates` | — | Insight |
| Billing: plan/subscription/boost | `commercial` | — | Billing |
| Org: members/invites/venue switch | `organisation_admin`, `organisation_overview` | — | Settings → Organisation |
| Assistant | `assistant` | Onboarding (first-run) | Overview card + shift/offer compose |

## Worker app (mobile) — 5 tabs, unchanged count

Five bottom tabs is the ergonomic ceiling (D069). The revamp keeps the five and **absorbs** the new
surfaces rather than adding tabs. Header carries the notification bell and a message icon.

**1. Browse** — *work you can get.* The ranked marketplace feed (M5) with search, filters, and the
existing map view. New here:
- A per-card **"why recommended"** line (already shipped) when ranking is on.
- A one-time **consent nudge** ("Use my history to rank shifts?") that sets profiling consent — shown
  only when ranking is on and consent is unset; dismissible.
- An **appeal action** on a card's overflow menu ("This shouldn't rank so low") → files a feed appeal.

**2. Shifts** — *work you have, and work offered directly to you.* Segmented:
- **Offers** (badge count) — pending named offers to accept/decline; the reason a manager sent it.
- **Upcoming** — confirmed bookings; check-in; release/cover request actions live on the booking.
- **Past** — completed/previous.
- Certification and risk warnings surface on the shift, not as a separate screen.

**3. Applications** — *work you asked for.* Waiting / Decided (unchanged model; visual refresh only).

**4. Earnings** — statements framed as **paid to you directly by the venue** (D071); the platform fee
is the venue's concern, not shown as the worker's. No wages ever move through the app.

**5. Profile** — *how venues see you* + **Settings** (drilled list, D070). Rows, each showing its
current value on the right:
- **Availability** — recurring rules, exceptions, time off (per venue). Framed as intent that informs,
  never auto-rejects (C4).
- **Certifications** — held certs + expiry warnings.
- **My venues** — relationships (permanent / pool / temp) and their status.
- **Auto-accept** — per-pool-venue standing rules (only replays a standing answer to an offer already
  addressed to the worker).
- **Privacy** — profiling consent toggle (mirrors the Browse nudge).
- **Notifications** — existing settings.
- **Account** — email, sign-out.

**Header:** notification bell (existing) + a **Messages** icon → thread list (M4). Onboarding
(assistant) shows once on first run, not as a permanent destination.

### Worker home mode (D069, preserved)
Employed workers open on **Shifts**; marketplace-only workers open on **Browse**; mixed workers get
both and the initial tab from work-context. This already exists — the revamp keeps it.

## Operator console (web) — grouped sidebar

Desktop tolerates more than five, but the current eight flat items will grow unwieldy as billing,
org, messaging and the approval queues arrive. Reorganise into a tighter grouped sidebar. Header
carries the venue chip + rating (D061), the notification bell, and a message icon.

**1. Overview** — the at-a-glance home (coverage, decisions, tonight, week strip). Positive-first
(D072). Carries the assistant **onboarding card** for new venues.

**2. Schedule** — the week board + rota builder + published revisions, with **Templates** as a
sub-view. The **named-offer** and **cover/release** action lives on the shift where it happens; the
four-field escalation policy is edited in Settings but its effects are visible here.

**3. Requests** — *the operator's decision inbox, unified.* One place for everything waiting on a
manager: applications to review, cover/release requests, availability/time-off approvals, and (for
staff/system role) feed-appeal review. Replaces hunting across screens. Each row is an action with a
count that is the true total (D068).

**4. People** — the directory: permanent / pool / temp in one list (D071), relationship status, live
status (available/away/booked, W6), join-code invitations, and certifications held. The worker
profile drills in here.

**5. Timesheets** — approve worked hours; export for the venue's own payroll (never pushed, D071).

**6. Insight** — the M4 cuts (cost-of-coverage, savings-available, team-building, fill/what-helps),
positive-first, presentable to prospective venues (D072).

**7. Billing** — statements (fee-only amount due, wages informational), plan/subscription, and boosts.
Significant enough to venues to warrant its own destination rather than hiding under Settings.

**8. Settings** — venue settings, the scheduling/escalation policy, **Organisation** (members,
invitations, roles, venue switching), Privacy/consent, account + sign-out (D061).

**Header:** venue chip + rating, notification bell, **Messages** icon → threads.

## Cross-cutting patterns

- **Assistant is ambient, never a destination.** It appears where the work is: the shift-post "help me
  write this" button (shipped), the offer-message compose helper, and the first-run onboarding card.
  Human-in-the-loop always (C4) — it drafts, the person edits and sends.
- **Approvals converge.** The worker never has an "approvals" concept; the operator gets exactly one
  (**Requests**). This is the single biggest usability win of the revamp.
- **Status is a word + a mark** (D069), never a loud coloured pill. Money is tabular figures.
- **Empty states are achievements** (D072): "every shift covered this month", not a blank chart.
- **Notifications + messages are header affordances** in both clients, not tabs.

## Open IA decisions (for you)

1. **Worker Shifts crowding** — Offers + Upcoming + Past under one tab with segments, or split Offers
   out? Recommendation: segments (keeps 5 tabs; offers are transient).
2. **Console Requests scope** — does the unified Requests inbox include applications, or do
   applications keep a dedicated destination? Recommendation: include them; one inbox is the win.
3. **Billing as its own nav item vs under Settings** — recommendation: its own item (venues care about
   money and will look for it directly).
4. **Templates** — sub-view of Schedule, or its own item? Recommendation: sub-view (it's a shortcut to
   posting, not a daily destination).
5. **Messages** — header icon (like the bell) or a full nav item? Recommendation: header icon in both,
   promote to a tab/nav item only if usage proves it central.

## Suggested build sequence (once visual direction is set)

1. Lock the visual system (your research: palette, type, components) — a shared kit both apps consume.
2. Worker app shell first (5 tabs + header), then screen-by-screen: Browse, Shifts (with Offers),
   Profile/Settings drilled list, Applications, Earnings.
3. Console shell (grouped sidebar + header), then Overview, Schedule, **Requests** (highest-value new
   surface), People, then Billing/Insight/Settings.
4. Wire the deferred M5 client surfaces as they land in their new homes (consent nudge + appeal in
   Browse; offer-message helper in Schedule; onboarding card in Overview).

Nothing here changes the API. The IA maps onto endpoints that already exist and are tested.
