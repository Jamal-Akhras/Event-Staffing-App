# Workforce Platform Requirements

Consolidated requirements for the pivot from a temp marketplace to an all-in-one workforce tool.

Requirements marked [brief] come from the meeting minutes and requirements sheet. Those marked
[review] come from the comment threads on the shared sheet. The rest are derived
from those, from the shared "Legal and Payment Model Summary" note, or from competitive research. That
note states on its own first page that it is a commercial and operational summary and not legal or tax
advice, so it is treated here as a starting point rather than as authority.

Naming: Workle is the current working name, Venue OS is the name in the codebase and in these
documents. They are the same product. Changing it is presentation-only, being eleven files across the
web and mobile clients and none in the API.

B2B is the target. Consumer hiring is a possible future direction, not a design driver.

This document is written to be shared and to be built from. The screens that come out of it are also
sales material, shown to prospective venues before those venues have any data of their own, which is
why section 7 sets a tone requirement alongside the functional ones.

## 0. Constraints

Non-negotiable. Everything else is designed inside these.

- C1 — Wages never pass through the platform, for permanent staff or temps. The venue pays the worker
  directly.

- C2 — The platform never submits timesheets or payment instructions to a payroll system on a worker's
  behalf. Venues pull data out, the platform never pushes.

- C3 — The platform charges the venue only. Workers are never charged a work-finding fee.

- C4 — No automated decision that materially affects a worker. Ranking and suggestion are permitted,
  automatic rejection, blocking or exclusion is not.

- C5 — The venue is the employer of its own permanent staff. The platform is software for that
  relationship, never a party to it.

## 1. Organisation and accounts

- O1 — [brief] A company can be set up with one or more sites under it.

- O2 — A group can share staff across its sites, and cover taken from another site of the same group
  carries no platform fee.

- O3 — Multiple managers per venue, with roles and permissions.

- O4 — An account with no permanent staff is fully usable. No rota is required to post and fill shifts.

- O5 — Spend and coverage roll up from site to group.

## 2. People and relationships

- P1 — [brief] A venue can manage permanent workers and hire temps as needed.

- P2 — [brief] A venue code lets existing staff join the venue's team.

- P3 — [brief] Sign-up clearly distinguishes joining a venue's team from joining the open temp pool.

- P4 — A person's relationship to a venue is explicit: permanent, part-time, bank, pool or one-off, with
  status, dates, contracted hours and agreed rate.

- P5 — Pool membership is separate from employment. A worker can be in a venue's private pool without
  being employed by it.

- P6 — One directory shows every person the venue deals with, being team, pool and past one-off workers,
  with relationship, rate and status visible.

- P7 — A person can be moved between relationships: temp into the pool, pool member into employment, and
  offboarded. Every transition is recorded because it changes what they cost.

- P8 — A person can hold relationships with several venues at once without duplicate accounts.

- P9 — [review] Badges for venues and for workers, earned on shifts posted, shifts attended and
  five-star reviews received. An incentive that applies to permanent staff as much as to temps.
  Explicitly not 1.0.

## 3. Scheduling

- S1 — [brief] A venue can schedule its existing employees.

- S2 — [brief] Gaps in the schedule can be filled with temps.

- S3 — A shift is assignable to a named person, offerable to the venue's pool, or publishable to the open
  market, and can move outward through those states.

- S4 — Unfilled or dropped slots escalate automatically: team, then pool, then market. [review] The
  venue controls the ladder and the delay at each step, including turning a step off. Nothing reaches
  the open market because the platform decided it should.

- S5 — A rota is published as an event. Staff are notified, and later revisions show what changed.

- S6 — Staff can request swaps and cover, subject to manager approval.

- S7 — Workers can record availability, unavailability and time off. Managers can approve it.

- S8 — The projected wage cost of a rota is visible while it is being built, before publication.

- S9 — The schedule presents as a job list rather than a week grid for accounts with no employment
  relationships.

## 4. Hiring and the marketplace

- M1 — [brief] Priority posting, meaning paid placement into the top 1, 5 or 10 of a role feed.

- M2 — Paid placement is labelled as such to the worker seeing it.

- M3 — The proportion of boosted slots in any feed is capped, and boosted placements are accounted for.

- M4 — The worker feed is ranked, not ordered by start time.

- M5 — A worker's feed is ordered by relationship: their venues first, then pools they belong to, then the
  open market.

- M6 — A venue can see applicant history, ratings and reliability before deciding.

## 5. Messaging

Raised in review as missing. Venues and workers have to be able to talk, and the shape of that is a
product decision, not an afterthought.

- N1 — [review] A venue and a worker can message each other in the app about a specific shift or
  application.

- N2 — [review] A shift has a group thread its assigned workers and the venue's managers share, so
  someone running late tells everyone at once rather than through separate messages.

- N3 — [review] The venue opens the conversation. A worker can reply, and can ask questions about a
  shift they have applied for, but cannot message a venue they have no connection to. The reason is
  spam: without it the open pool becomes a channel for cold approaches to venues.

- N4 — [review] Messaging is two-way once opened, so both sides can ask questions before either
  commits. A venue judges suitability and a worker judges the job without a booking existing yet.

- N5 — [review] A permanent or part-time worker has a standing channel to their managers that does
  not depend on a shift being open. Employment is continuous, so the conversation is too.

- N6 — Messages are part of the record: retained, exportable and covered by the same audit trail as
  everything else.

## 6. Hours and timesheets

- H1 — Attendance is captured for both rota'd staff and temps, with a lighter path for permanent employees
  than the two-party PIN.

- H2 — A manager can review and approve worked hours for a week across permanent and temp workers
  together.

- H3 — Edits to approved hours are recorded against the original.

- H4 — Approved hours can be exported for the venue's own payroll, initiated by the venue.

## 7. Money and billing

- B1 — [brief] Permanent workers are free to add and manage under the monthly fee.

- B2 — [brief] A tiered commercial model: a free tier charging a percentage per filled shift, a
  subscription tier where a venue's own pool is free and outside hires are charged, and an enterprise
  tier. Exact prices to be set.

- B3 — [brief] Statements cover permanent and temp workers together.

- B4 — Statements distinguish unmistakably between wage cost, which is information for the venue and owed
  to workers, and platform fees, which are the only amount owed to us.

- B5 — The platform fee is a function of plan and of the worker's relationship to the venue at the time of
  the shift.

- B6 — Rostering a permanent employee never generates a platform fee.

- B7 — Recurring subscription billing, alongside per-shift fees.

- B8 — Priority-posting charges appear as their own line, frozen at purchase.

- B9 — Every charge is frozen when incurred and never recomputed from live rates.

## 8. Insight

The reason a venue keeps paying, and the part of the product most likely to be seen before a venue has
signed up. Only possible because both sides sit in one product.

Tone requirement: insight is framed as opportunity and next action, never as blame. Lead with what is
working and what can be improved. Do not put a venue's failures in the primary row. This is not about
hiding problems, since an unfilled shift still has to be visible and explained. It is about which
number is largest on the page and how it is worded. A screen shown to a prospective venue should make
them feel capable, not audited.

- I1 — Coverage ahead: how much of the coming period is covered, and which shifts still have room.

- I2 — Cost of coverage: wages plus platform fees per covered hour, split by source, being own team, pool
  and market.

- I3 — Savings available: shifts that could be covered by the venue's own available team at no platform
  fee.

- I4 — What helps shifts fill: the conditions of rate, lead time and day under which this venue's shifts
  fill fastest, and which upcoming shifts fall outside them.

- I5 — Pool strength: how many reliable workers the venue can call on, and how that is growing.

- I6 — The value of planning ahead: what earlier posting is worth compared with last-minute cover.

- I7 — Team building: how much of the venue's work is covered by returning faces rather than strangers.

- I8 — Every figure reflects all matching records, never a truncated page.

- I9 — Empty and healthy states read as achievements, not as blanks. "Every shift covered this month"
  rather than an empty chart.

- I10 — [review] The venue can reach all of its data. The figures given prominence are a chosen
  subset, being the ones that show the platform earning its fee. Breadth underneath, selection on
  top.

## 9. Worker app

- W1 — One app for every kind of worker.

- W2 — The home surface depends on relationship: rota first for employed staff, marketplace first for
  temps, both for people who are both.

- W3 — Workers see assigned shifts, offered shifts and open shifts as distinct things.

- W4 — Workers can record availability and request time off.

- W5 — Workers see their own hours and what each shift paid, as a record, not as a balance held by the
  platform.

- W6 — [review] A worker's profile carries a current status drawn from their availability and
  bookings, being available, booked, away or unavailable, visible to venues they have a relationship
  with. W4 records the underlying availability; this is how it reads at a glance.

- W7 — [review] Workers record their certifications with expiry dates, and are prompted before one
  lapses.

## 10. AI

Four use cases. Two can ship without data, two need a pilot's history first.

Two conditions were set in review and bind all of them: the assistant is never forced into a flow a
manager can complete without it, and running cost has to stay near zero. A self-hosted model is the
route being explored for the second, accepting that it will be slower, and it depends on what the
product is eventually hosted on. This section needs a dedicated session before any of it is built.

- A1 — [brief] Onboarding helper, assisting company setup and writing shift posts. Ships early, needs no
  training data, low risk.

- A2 — [brief] Pricing assistant, predicting whether a shift will fill at a given rate, timing and lead
  time, before it is posted. Highest value, needs pilot data.

- A3 — [brief] Shift filling, being ranking and notification targeting to get the right shift in front of
  the right workers. Needs pilot data and the ranking layer from M4.

- A4 — [brief] Suggested workers, proposing candidates to a human who decides. Viable but the riskiest.

- A5 — [review] Suggestions draw on the venue's own team and pool before reaching to the market,
  using availability, contracted hours and who has worked that shift before. The cheapest option is
  offered first because it is usually also the best one.

- A6 — [review] The assistant can draft the message a manager sends when offering a shift, for the
  manager to edit and send. Whether it can also send, doing the reach-out on the manager's behalf,
  was raised in review and is not settled. See Q8.

- A7 — Any suggestion or ranking affecting a worker is explainable, appealable and reviewable by a person.

- A8 — Models are trained only on data collected under a recorded lawful basis.

- A9 — [review] Cost of running the assistant is a design constraint, not an afterthought. Each use
  case has to justify its per-call cost or run on cheaper local logic. See Q9.

## 11. Compliance

Under the direct-engagement model the venue is the employer, so most employment duties are the venue's.
The platform's job is largely to carry information, not to verify it. Two duties do not delegate and
are marked.

Unresolved: the shared legal and payment note lists right to work, suitability, health and safety and
insurance under "compliance obligations in both models", implying they fall on the platform regardless.
The position below reads them as the venue's. Neither reading is authoritative, since that note is
explicitly not legal advice, so this needs a solicitor. See Q6.

- L1 — The venue performs the statutory right-to-work check. The penalty for illegal working is the
  employer's. The platform collects the worker's declaration and evidence and surfaces it to the venue
  so the check is quick. [review] Both founders would rather the platform ran the check itself, on the
  same make-it-easy-for-the-venue reasoning as the rest of the product. Whether that is legally
  available, and whether it moves the penalty onto us, is the question. The text above stands until
  it is answered. See Q6.

- L2 — A shift can require a certification, and only workers holding a current one can be assigned or
  apply. Workers record certifications on their profile with expiry dates; the venue chooses which a
  shift needs. Covers DBS, SIA, first aid, food hygiene, personal licence and any other qualification
  the venue names. Does not delegate: for roles where the certificate is required by law rather than
  by preference, the platform must not place a worker without it.

- L3 — Health and safety: the venue supplies role, location and risk information, and the platform
  passes it to the worker before the assignment. Does not delegate: an agency must obtain this from
  the hirer and give it to the work-seeker, so it is a required field on the shift, not an optional
  one. [review] Carrying this information was questioned as a litigation exposure. The counter-view,
  and the one this requirement follows, is that it has to go through the app anyway: centralising it
  is the point of the product, and it becomes load-bearing the moment we take on events work. Needs
  the same legal answer as L1.

- L4 — Records of introductions and assignments, and a clear written description of the platform's role in
  every agreement.

- L5 — Objective matching criteria, a non-discrimination policy, moderation of abusive or
  discriminatory reviews, and a documented appeals process. Binds the ranking layer and every AI
  feature. [review] The appeals process has to cover both sides, and has to accept a report of
  something seriously wrong as well as a disputed score. Scope of it is open. See Q7.

- L6 — Separate written terms for the venue, permanent staff and temp workers, plus privacy policy,
  acceptable-use policy, rating policy, cancellation and no-show policy, and a complaints process.

- L7 — Data protection: ICO registration and fee where required, privacy notice, recorded lawful basis,
  secure storage and a retention policy.

- L8 — Subject access, correction and erasure processes, honouring requests made verbally or in writing.

- L9 — Consent and a recorded lawful basis are in place before any profiling or ranking of people begins.

- L10 — A venue sees its aggregate worker rating, never which worker gave which score. Attribution
  would expose workers to retaliation on their next application. [review] Agreed in review.

- L11 — Full audit trail of who changed what, already in place and to be maintained through the pivot.

Insurance, meaning public liability, professional indemnity and cyber, is risk management rather than a
licence to operate, and is deferred. One exception to diarise: employers' liability cover becomes
legally required as soon as we employ anyone ourselves.

## 12. Structure

Four structural rules. Each is needed by a customer the product already has to serve, being an event
company with no rota, a single site with no group, or a venue with no logo. Each also happens to keep
later options open at no extra cost today.

- X1 — The shift is the atomic unit. Rotas, pools and teams are layers above it, never prerequisites for
  creating one.

- X2 — Nothing assumes a shift's owner has employees, a rota, a subscription, or more than one site.

- X3 — Billing computes from plan plus worker relationship, not from an assumption that every account
  carries a subscription.

- X4 — Location on a shift is an address. It is not tied to a venue's registered premises.

## Out of scope

Recorded so scope creep is visible when it happens.

- Running payroll, holding wages, or paying workers.
- HR records, meaning contracts, documents, performance management and disciplinary.
- Multi-shift or open-ended placements. Hiring stays shift by shift.
- Consumer hiring. A possible later direction, needing its own legal structure, and not a design driver
  now.
- Automated hiring or rejection decisions.

## Open decisions

- Q1 — Pricing: exact tiers and amounts.

- Q2 — What "site" means for pricing: venue, physical location, or organisation.

- Q3 — Whether free permanent workers are capped per site.

- Q4 — Paid-placement disclosure requirements, confirmed with the solicitor.

- Q5 — Written confirmation of the agency position in section 0.

- Q6 — Which of right to work, worker suitability, health and safety and insurance fall on the
  platform rather than the venue under direct engagement, and how much of each we are allowed to take
  on voluntarily. Both founders would prefer to run right-to-work checks in the app if that is legally
  available, which is the opposite of what L1 currently says. The shared note and section 11 disagree,
  and neither is authoritative. This is the solicitor question.

- Q7 — Whether reviews can be challenged, and by whom. Raised in review as a fairness question, for
  venues and workers alike, together with a route for reporting something seriously wrong. The doubt
  attached to it is jurisdiction: what standing we have to adjudicate between two parties whose
  employment relationship we are not part of. L5 assumes a process exists. UNRESOLVED.

- Q8 — How far the assistant goes in messaging workers on a manager's behalf. A6 stops at drafting a
  message the manager sends. Sending it directly was raised in review and would cross C4 if a worker
  read it as a decision rather than an approach.

- Q9 — Which AI use cases justify their running cost, and which should be cheaper local logic rather
  than a model call. Depends on whether a self-hosted model is fast enough on the hosting we end up
  with. Needs its own session.
