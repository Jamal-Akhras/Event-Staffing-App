# Decisions and Open Questions

This is the discussion agenda for product and technical choices. A decision belongs here when it changes users, risk, cost, architecture or the launch plan. Detailed design stays in the relevant linked document.

## Active decisions

| Decision | Current direction | Why it matters |
|---|---|---|
| Initial market | Hospitality first; Bath is the proposed pilot | A narrow market improves the chance of useful supply-and-demand density |
| Architecture | Keep the modular monolith and managed PostgreSQL | The product needs hardening and validation, not a rewrite |
| Tenancy | One organisation may own several isolated venues | Prevents customer data leakage and supports future multi-venue operators |
| Payments today | Venues pay workers directly; the app records an attestation | Avoids implying processor money movement that does not exist |
| Worker pricing | Keep work-finding free for workers | Aligns the proposed model with an employer-paid service |
| Marketplace expansion | Repeat hospitality city by city before broad categories | Reduces the risk of a broad but empty marketplace |
| Founding partners | Waive only the platform fee, using bounded terms | Worker wages and statutory costs still need funding |
| Infrastructure | No Kafka or Kubernetes now | Their operational cost is not justified by the current service count |
| Documentation | One shared library for founders and engineers | Product and technical trade-offs stay visible in the same conversation |

## Decisions required before public launch

| Topic | Options to discuss | Working recommendation | Status |
|---|---|---|---|
| Legal operating role | Employment business, employment agency, or narrower software marketplace | Obtain UK specialist advice against the exact workflow | Open |
| Pilot geography | Bath or another city | Bath, if both venue demand and worker supply can be recruited | Proposed |
| Initial roles | Broad hospitality or a limited role set | Start with the smallest set that has repeated venue demand | Open |
| Venue types | Restaurants, pubs, hotels, events, or a subset | Choose based on founder access and frequency of shifts | Open |
| Standard employer fee | Per completed shift, subscription, hybrid, urgent-listing fee | Test manually before building billing automation | Open |
| Direct hiring | Free conversion, transfer fee, or extended-hire policy | Support it explicitly; avoid punitive worker restrictions | Proposed |
| Launch channel | Private hosted demo, controlled beta, or public stores | Controlled beta until support and compliance operations are staffed | Open |
| Identity provider | Managed authentication or custom Google/Apple OIDC | Prefer managed unless product constraints justify owning the protocol | Open |

## Founding-partner questions

The technical direction is recorded in [founding-partner entitlements](../80-future/founding-partner-entitlements.md). The business rules are still open:

- How long does the fee waiver last?
- Is there also a completed-shift cap?
- How many times can a code be redeemed?
- Does one entitlement cover every venue in the organisation?
- What normal fee is displayed beside the waiver from day one?
- Can a founder manually extend or revoke the entitlement, and under what audit policy?

## Production ownership questions

- Who owns the cloud, storage, email, Sentry, Apple and Google accounts?
- Which support and privacy contacts appear in the product and contracts?
- What backup retention period, recovery target and incident contact are funded?
- Who reviews reports and safety incidents, and during which hours?
- Which launch metrics are reviewed weekly, and who can stop expansion when quality falls?

## How to record a decision

Use a short entry with a stable ID, date, status, owner and consequence:

```text
D### ACTIVE — Decision in one sentence.
Reason: why this option won.
Consequence: what becomes easier, harder or impossible.
Review trigger: the evidence that should make us reconsider it.
```

A decision is not permanent merely because it is written down. The review trigger prevents the team from relitigating choices without new evidence while still allowing the product to learn.
