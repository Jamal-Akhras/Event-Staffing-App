# Workforce Pivot Plan

## What is changing

Venue OS moves from a one-off temp marketplace to a workforce management tool. A venue manages its
existing workers, its own pool, and one-off temps in the same place: scheduling them, seeing what they
cost, and producing statements across all three. The wider market problem is that temp tools only
handle the gap, so a venue still runs its real roster somewhere else.

The temp marketplace does not go away. It becomes the overflow behind a roster the venue already keeps
in the product.

## Settled scope

| Question | Answer |
| --- | --- |
| Does the platform pay workers? | **No.** Wages never pass through the app, for permanent staff or temps. |
| How far does management go? | Organise workers, schedule them, see cost, produce statements. Not HR records, contracts or performance management. |
| Can a temp be placed for longer than one shift? | No. Shift by shift stays. "Employment agency" describes the legal posture, not the booking length. |
| Do venues get hours out for payroll? | Yes. Approved timesheets exported for the venue to run its own payroll. |
| One worker app or two? | One app, different home: a permanent employee opens onto their rota, a temp onto the marketplace. |

The first answer settles the legal position that was open through the pricing review: Venue OS is a
direct-engagement employment agency and shift-management platform. The venue contracts with and pays
the worker. Venue OS charges the venue only.

### The one trap in timesheet export

For **permanent staff** there is no issue: they are the venue's own employees and the hours are the
venue's own data.

For **temp workers** the Conduct Regulations matter. Exporting approved hours *to the venue* is fine —
they are the engager and the payer. Venue OS submitting timesheets into a venue's payroll portal, or
passing a worker's bank details to a payroll provider, is expressly called out as arranging payment
and would make the platform an employment business.

**Rule: the venue pulls, the platform never pushes.** Download and venue-initiated integrations only.

## Commercial model

| Tier | Price | Fee |
| --- | --- | --- |
| Classic | £0 per month | 10% on shifts filled from the flexible pool |
| Plus | From £25 per month, per site | 0% when hiring from your own pool, 10% for anyone else |
| Enterprise | Custom | Larger venues; own branded app in the app stores |

Permanent workers are free to add and manage under the monthly fee. The structure is deliberate: Plus
pays a venue to bring its own staff onto the platform, because doing so makes those hires free — the
same behaviour the pivot depends on. The 10% on outside hires funds the marketplace that makes the
pool worth having.

**Accepted leakage.** Under Plus a venue can hire someone once at 10%, add them to its pool, and hire
them free from then on. That is the model working — paid for the introduction, then monthly for the
tooling — but it should be a chosen position rather than a surprise.

**Not being copied** from the reference pricing card: "we take care of all employment obligations" and
"automated payment/payroll". Those are employment-business commitments. The tier structure is adopted;
those promises are not.

## Decisions still open

| Ref | Decision | Why it blocks work |
| --- | --- | --- |
| D3 | Define "site" for the Plus price: venue, physical location, or organisation | The schema separates organisation from venue; pricing has to map onto one |
| D4 | Review paid ranking for disclosure requirements | Priority posting sells position in a worker's feed; disclosure changes the UI, not a footnote |
| D5 | Set the boundary on free permanent workers: unlimited per site, or capped | Billing has to know what happens at the limit |
| D6 | Confirm the settled position above with the solicitor, in writing | Everything is designed around wages staying outside the platform |

## 1. Data model

The system knows one kind of worker today: a marketplace applicant. It now needs to know a person can
be employed by a venue, in that venue's private pool, in the open market, or several at once.

- **A1** Employment relationship between venue and worker: type (permanent, part-time, bank, temp),
  status, start and end dates, contracted hours, agreed rate. The spine of the pivot.
- **A2** Pool membership, separate from employment: discoverable only by their venue, or by the wider
  market. The Plus fee cannot be computed without it.
- **A3** Venue join codes so a manager can invite existing staff: code, venue, default role, expiry,
  usage limit, who redeemed it. Reuses the shape of the partner-code table.
- **A4** Shift origin: assigned to a named worker, offered to the venue's pool, or published to the
  market. Today every shift is published and waits for applications.
- **A5** Worker availability and unavailability, including recurring patterns and time off.
- **A6** Record the worker's relationship on `booking_charges` at freeze time, because the fee depends
  on whether they were pool or market on that day.
- **A7** Mark permanent shifts as non-billable so a rota'd employee never generates a platform fee.

## 2. Scheduling

The largest genuinely new build. Posting a shift and waiting is a marketplace; assigning a named
person to a slot is a rota, and it is a different interaction end to end.

- **B1** Rota builder: assign named staff across a week, showing who is over or under contracted hours.
- **B2** Publish a rota as an event, so staff are notified and revisions show a clear diff.
- **B3** **Gap escalation:** an unassigned or dropped slot offers to the venue's pool, then to the wider
  market after a delay. The product thesis in one feature.
- **B4** Shift swaps and cover requests between staff, with manager approval.
- **B5** Availability and time-off capture in the worker app, with approval in the console.
- **B6** Live cost of the rota as it is built: projected wage cost for the week, per day and per role,
  before it is published.

## 3. People

Named directly in the requirements and not previously broken out.

- **P1** Worker directory: every person the venue deals with in one list — permanent staff, pool
  members, one-off temps — with their relationship, rate and status made obvious.
- **P2** Worker detail: history with this venue, hours, cost to date, reliability, ratings, and which
  pool they sit in.
- **P3** Move someone between relationships: invite a temp into the pool, make a pool worker permanent,
  offboard a leaver. Each transition is recorded, since it changes what they cost.

## 4. Hours and timesheets

- **T1** Timesheet view: approved hours for a week across permanent and temp workers together.
- **T2** Manager approval of hours, with edits recorded against the original.
- **T3** Export approved hours as CSV for the venue's payroll, and venue-initiated integrations later.
  Pull only — see the trap above.
- **T4** Extend attendance capture to rota'd staff. The two-party PIN was designed for one-off temps;
  a permanent employee clocking in needs a lighter path.

## 5. Marketplace and priority posting

- **C1** Build a ranking layer for the worker feed. It is `ORDER BY start_time` today, and priority
  posting, suggested workers and any AI ranking all sit on top of it.
- **C2** Priority tiers: paid boost into the top 1, 5 or 10 of a role feed, with the paid slot labelled.
- **C3** Cap and account for boosted slots. A feed workers stop trusting stops filling shifts, which
  destroys the thing being sold.
- **C4** Split the worker feed by relationship: my venues first, then my pools, then open market.

## 6. Billing and statements

- **E1** Subscription billing per site alongside the per-shift fee. Nothing charges recurring today.
- **E2** Fee percentage becomes a function of plan and worker relationship. `PLATFORM_FEE_PERCENT` is
  one number for everyone; Plus needs 0% inside the pool and 10% outside it.
- **E3** Combined statement covering permanent and temp workers together: hours and wage cost per
  person as information for the venue, and separately the platform fees actually owed. The distinction
  has to be unmistakable on the page, because only the second is a bill from Venue OS.
- **E4** Priority-posting charges as a separate billable line, frozen at purchase.

## 7. Onboarding and identity

- **F1** Branch sign-up: joining a venue's team by code, or joining the open pool. Sets the person's
  relationship from the first screen.
- **F2** Company setup flow: create the organisation, add sites, invite managers, invite staff.
- **F3** Manager roles and permissions within a venue.
- **F4** Worker app home switches on relationship: rota first for permanent staff, marketplace first
  for temps, both for people who are both.

## 8. AI

All four named use cases are reasonable. Two can ship without data; two need a pilot's history first.

| Use case | Position |
| --- | --- |
| Onboarding helper | Ship early. Guiding company setup and shift writing needs no training data and is low risk. |
| Pricing assistant | Highest value. "Sunday lunch at £12.50 fills 40% of the time" is advice before posting. Needs pilot data. |
| Shift filling | Ranking plus notification targeting. Sits on C1. Needs pilot data. |
| Suggested workers | Viable but riskiest. Must suggest to a human, never decide, never silently exclude. |

- **G1** Write the guardrail before the feature: no automated decision materially affecting a worker,
  appealable outcomes, human review for restrictions. Ranking shifts for a worker is fine because they
  still choose; auto-declining an applicant is not.
- **G2** Ship the onboarding and shift-writing assistant during the pilot.
- **G3** Treat the pilot as data collection for the pricing assistant and ranking.

## 9. Compliance

- **H1** Consent and lawful-basis records before any profiling or ranking goes live. A hard dependency
  of C1 and every AI item.
- **H2** Right-to-work checks before a first shift, with secure records and follow-ups.
- **H3** Written terms for three relationships: venue, permanent staff, temp worker.

## What carries over

The pivot is smaller than the requirements sheet makes it look.

Unchanged and still correct: the event log and audit trail, booking transitions, frozen
`booking_charges`, two-party attendance PINs, the `/insights` aggregates, mutual ratings and
reliability, the organisation/venue/market hierarchy, and the design language across both apps.

Extended rather than replaced: shifts gain an origin and an assignee, charges gain a relationship
snapshot, the feed gains a ranking layer, billing gains a subscription. The booking lifecycle —
requested, confirmed, checked in, checked out, approved, paid — works for a rota'd shift exactly as it
does for a temp one, which is why shift-by-shift placement keeps the build small.

## Suggested order

D3 to D6 first, because they change the specification rather than the schedule. Then A1 to A4, A7 and
F1, which everything else reads from. Then P1 to P3, which is the cheapest visible proof of the pivot —
a venue seeing all three kinds of worker in one list. Then B1 to B3 and B6, the product thesis. T1 to
T3 next, since timesheet export is the strongest reason a venue switches. C1 unlocks priority posting
and every AI item. Billing last.

**Scoping note.** B1 to B6 is a rota product, and rota products are where most workforce tools spend
their first two years. If the Bath pilot is meant to run soon, the honest minimum is A1 to A4, A7, F1,
P1 and B3 — let a venue register its own staff, see them all in one place, and have unfilled slots fall
through to the temp pool — with full rota building after. That tests the thesis without building a
scheduling suite first.
