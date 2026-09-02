# Merging Management and Hiring

How the venue-side workforce tool and the worker-side marketplace become one product rather than two
bolted together. Written as options with a recommendation, not a settled design.

## What the market actually looks like

Two camps, and neither covers the whole job.

**Scheduling tools** — Deputy, Planday, 7shifts. Strong rota building, labour cost, and internal gap
filling: 7shifts' Shift Pool lets your own staff bid on open shifts with manager approval. What they do
not do is reach outside the business. When nobody on your team can cover Friday, the software stops
helping and the manager starts texting.

**Staffing marketplaces** — Indeed Flex, Coople, Limber. Strong at finding strangers fast, with
verified profiles, ratings and favourites. Their scheduling is thin, and it schedules *flexible*
workers rather than the venue's whole team. Your salaried head chef does not exist in these products.

**Coople is the closest to the merge.** It advertises combining internal staff, payrolled workers and
new talent into pools, planned from one place. It is the sharpest competitor to this direction.

**The differentiator, and it cuts both ways.** Limber and Coople both handle payroll. Venue OS
deliberately will not. That makes it cheaper and simpler, with no wage markup and no reason for a
venue to change how it pays people — but it also means the product cannot lean on "we take the admin
away". It has to win on **visibility and coverage** instead, which is exactly the stated goal.

## The tension to design against

Managing people you employ and hiring people you do not are different mental models.

Management is about names, contracted hours, obligations and cost control. Hiring is about roles,
availability, risk and speed. If the product exposes them as two destinations — a "Team" tab and a
"Marketplace" tab — the venue experiences two tools with one login, and the all-in-one claim is false
on the first screen.

The merge has to happen in the interface, not just the database.

## Three ways to merge

### Option 1 — The rota is the product, the market is a state

There is no marketplace destination. There is a schedule, and every slot on it is in one of three
states: **assigned** to a named person, **offered** to your pool, or **open** to the market. A manager
drags a name onto Friday; if nobody fits, the same slot is released outward without leaving the screen.

*Strength.* Matches how a manager actually thinks — "Friday needs covering" — and makes hiring feel
like a feature of scheduling rather than a separate errand. Strongest answer to "all in one".

*Weakness.* Buries the marketplace. A venue that mostly hires temps and barely rotas may find the
product asks them to build a schedule they do not want.

### Option 2 — Concentric rings of workforce

One People surface, organised by closeness: **your team**, then **your pool**, then **the Bath
market**. Hiring is widening the circle rather than switching context. Adding a good temp to your pool
is the natural next step after a shift goes well, and the rota draws from whichever ring you allow.

*Strength.* Makes the commercial model legible without a pricing page — the closer the ring, the
cheaper the hire. It also gives the pool a reason to exist in the interface, not just in billing.

*Weakness.* Rings are a people idea, and most of a manager's day is a time problem. On its own it does
not tell you Friday is short.

### Option 3 — Coverage is the headline

The home screen answers one question: **are you covered?** Every day ahead is covered, at risk, or
open. Drilling into a gap offers the ways to fill it in ascending cost — your own staff first, then
your pool, then the market — with the fee shown against each.

*Strength.* Turns the product into an operational instrument rather than a record-keeping one, which is
the stated ambition. It also makes the fee structure feel helpful instead of extractive, because the
cheapest option is always offered first.

*Weakness.* A single metric flattens things. Coverage does not capture cost overruns, and a venue
fully covered but 20% over budget would see all green.

## Recommendation

**Use all three, layered — but the spine is the shift, not the rota.**

An earlier draft made the rota the spine. That breaks at both ends of the customer range: a consumer
booking one bartender has no schedule to build, and an event company with no permanent staff would be
shown an empty rota nagging to be filled. The correction:

**The shift is the atom. The rota is what appears once you have people to assign. The market is where
a shift goes when nobody closer takes it.**

That scales in both directions from the same object, which is what lets one product serve a chain and
a wedding.

- **The rota is a layer, not a requirement** (Option 1). One schedule holds every kind of worker, and
  it appears when the venue has a team. There is no marketplace tab at any tier.
- **Coverage is the headline** (Option 3). The Overview leads with what is at risk and what it will
  cost to fix, so the tool tells the owner something rather than waiting to be read.
- **People are rings** (Option 2). The People surface shows team, pool and market as degrees of
  closeness, and moving someone inward is a first-class action.

The navigation that falls out of that is short, and notably contains no word for "marketplace":

| Tab | Answers |
| --- | --- |
| Overview | Am I covered, and what is it costing me? |
| Schedule | Who is working, and where are the gaps? |
| People | Who can I call on, and how close are they? |
| Hours | What did they work, and what do I owe them? |
| Insight | What should I change? |

Hiring appears inside Schedule when a slot cannot be filled internally, and inside People when a temp
is worth keeping. It is never a place you go.

## The insight only the merge makes possible

This is the part neither camp can copy, and it is the strongest argument for the pivot. A scheduling
tool does not know market rates. A marketplace does not know your salaried team. Holding both means
Venue OS can answer questions nobody else can:

- **True cost of coverage.** Wages plus platform fees per covered hour, split by source: your own
  staff, your pool, the open market.
- **Money left on the table.** "You paid market rate for three shifts that two of your own
  part-timers were free for." That single sentence justifies the subscription.
- **Coverage risk ahead of time.** Which of next month's shifts are likely to go unfilled, based on
  the fill history already being collected.
- **Pool health.** Are your regulars still active, or has your reliable bench quietly drifted to other
  venues?
- **Cost of flexibility.** What the venue pays for last-minute cover versus planned cover, which is the
  number that changes behaviour.

The gaps block already built for Analytics is the first of these. The rest need the relationship data
model from the pivot plan, and then they are mostly queries rather than new systems.

## How this changes the plan

Nothing in `workforce-pivot-plan.md` is invalidated, but three items get reframed:

- **B3, gap escalation**, stops being a feature and becomes the core interaction. It is where the two
  halves of the product meet.
- **P1, the worker directory**, becomes the rings view rather than a flat list.
- **A new item.** Cost-of-coverage reporting, splitting spend by source, which is the insight layer
  above. It depends on `booking_charges` carrying the relationship snapshot (A6), which is already
  planned.

## Serving organisations of all kinds

The same three objects have to carry very different customers. What changes is how much of the product
switches on.

| Customer | Has a team? | What they see |
| --- | --- | --- |
| Multi-site group | Yes, across sites | Full rota, cross-site staff sharing, spend rolled up by site |
| Single venue | Yes | Full rota, one site, coverage and cost |
| Event company | Rarely | No standing rota. A list of jobs at client locations, filled from pool and market |
| Consumer | No | One request. No schedule, no team, no subscription |

Two consequences.

**Rings gain a layer for groups.** For a chain the order becomes: this site's team, then the group's
other sites, then the group's pool, then the market. Cross-site cover is a real feature for anyone with
more than one location, and it is free money for them — a shift covered from another site costs no
platform fee. Worth building because it makes the group tier obviously worth paying for.

**The rota has to disappear cleanly.** For an event company or a consumer the schedule surface should
present as a list of jobs, not an empty week grid. Same data, different default view, chosen by whether
the account has any employment relationships.

## Going B2C, and the problem it creates

Opening one-off hiring to consumers is the largest expansion available: a wedding, a birthday, a house
party. It also fixes marketplace liquidity, because consumer demand fills the midweek and seasonal
troughs that venue demand leaves empty.

**But the payment model does not survive the move, and this is not a small detail.**

Everything decided so far rests on one fact: the venue employs and pays the worker, so wages never
touch the platform. A consumer cannot do that. A private individual hiring a bartender for six hours
does not run payroll, cannot operate PAYE, and has no HR function. The three ways out are all
consequential:

1. **The worker is self-employed for that engagement.** Plausible for genuinely casual one-off work,
   but employment status is decided by the facts of the arrangement, not by what the contract says. It
   needs advice, not an assumption.
2. **The consumer pays the worker directly, in cash or by transfer.** Legally simplest and consistent
   with the current model, but it is a poor experience, it is unenforceable, and disputes will land on
   the platform anyway.
3. **The platform handles the payment.** Solves the experience, and makes Venue OS an employment
   business — the model explicitly rejected, with payroll, employer National Insurance, holiday pay
   and insurance behind it.

**This should go to the solicitor as its own question**, separate from the venue model. It is entirely
possible the answer is that B2C requires a different legal structure from B2B, in which case it is a
later, deliberate phase rather than an extension of the same product.

Three other things change for consumers:

- **Trust becomes the product.** A venue hires into a workplace with other staff present. A consumer
  invites a stranger into their home. Verification, insurance and a real dispute process stop being
  compliance items and become the reason someone books at all.
- **Consumer protection law applies.** Cancellation rights, pricing transparency and terms written for
  a consumer rather than a business.
- **No subscription.** A consumer will not pay monthly for one party, so B2C is a pure per-booking fee
  — effectively the Classic tier with a different name.

## Sequencing

B2B first, unchanged. The venue product is where the legal position is settled, the pricing works, and
the pilot is already scoped.

B2C is a **phase two with its own legal review**, not a checkbox on the existing build. The useful
preparation is architectural rather than commercial: keep the shift as the atom, do not assume every
requester is an organisation, and avoid hard-coding a venue into the shift model. Doing that now costs
almost nothing and keeps the door open.

## Sources

- [7shifts](https://www.7shifts.com/restaurant-employee-scheduling-software/) — Shift Pool, internal bidding on open shifts
- [Planday hospitality](https://www.planday.com/industry/hospitality/) — drag-and-drop rota, shift templates
- [Coople Flex Work Platform](https://www.coople.com/uk/staffing-solutions/coopleflex/) — internal and external workers planned from one place
- [Limber](https://limber.work/) — favourite-staff teams that pick up shifts, with payroll handled
- [Indeed Flex talent marketplace](https://indeedflex.com/employers/lp/talent-marketplace/) — pre-verified workers, smart matching, VMS
