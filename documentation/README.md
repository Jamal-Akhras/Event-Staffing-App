# Event Staffing App Documentation

This is the canonical guide to the whole product: what it is, how people use it, how it is built, what is ready, and what still needs a decision. It is written for founders and engineers together. Technical terms are explained where they first matter, and implementation detail stays beside its product consequence.

**Verified against:** `main` at `39cf8fb`, 26 August 2026

**Current database revision:** Alembic `029_idempotency_records`

## How to read this library

Start with the [product overview](00-product/product-overview.md), then use the route that fits the conversation:

| Question | Start here |
|---|---|
| What does the product do today? | [Feature status and roadmap](00-product/feature-status-and-roadmap.md) |
| What decisions do we still need to make? | [Decisions and open questions](00-product/decisions-and-open-questions.md) |
| How does the whole system fit together? | [System architecture](10-architecture/system-architecture.md) |
| How do accounts and venues work? | [Accounts, identity and tenancy](20-domain/accounts-identity-and-tenancy.md) |
| How does a shift become completed work? | [Marketplace lifecycle](20-domain/marketplace-lifecycle.md) |
| What data do we store? | [Database design](30-data/database-design.md) |
| What APIs exist? | [Endpoint reference](40-api/endpoint-reference.md) |
| Can we launch it safely? | [Testing and production readiness](70-quality/testing-and-production-readiness.md) |
| How should founding-partner codes work? | [Founding-partner entitlements](80-future/founding-partner-entitlements.md) |

## Status language

Every document uses the same labels:

- **Implemented**: present in the current mounted product and verified in code or tests.
- **Partial**: usable foundations exist, but an important launch or scale requirement is missing.
- **Planned**: agreed direction, not current behaviour.
- **Proposed**: a recommendation that still needs a founder decision.
- **Gap**: needed for the intended outcome but not implemented.
- **Deferred**: deliberately postponed.
- **Historical**: useful context that is no longer authoritative.

When prose and code disagree, current code and tests win. A document must be updated in the same change that alters a public contract, business rule, schema, operational process, or product decision.

## Library map

### Product

- [Product overview](00-product/product-overview.md)
- [Feature status and roadmap](00-product/feature-status-and-roadmap.md)
- [Decisions and open questions](00-product/decisions-and-open-questions.md)

### Architecture

- [System architecture](10-architecture/system-architecture.md)
- [Backend architecture](10-architecture/backend-architecture.md)
- [Web and mobile architecture](10-architecture/web-and-mobile-architecture.md)
- [Security and privacy](10-architecture/security-and-privacy.md)

### Business domains

- [Accounts, identity and tenancy](20-domain/accounts-identity-and-tenancy.md)
- [Marketplace lifecycle](20-domain/marketplace-lifecycle.md)
- [Discovery, communications and trust](20-domain/discovery-communications-and-trust.md)
- [Payments and commercial model](20-domain/payments-and-commercial-model.md)

### Data and APIs

- [Database design](30-data/database-design.md)
- [Events, storage and data lifecycle](30-data/events-storage-and-data-lifecycle.md)
- [API design](40-api/api-design.md)
- [Endpoint reference](40-api/endpoint-reference.md)

### Flows, operations and quality

- [End-to-end flows](50-flows/end-to-end-flows.md)
- [Deployment and operations](60-operations/deployment-and-operations.md)
- [Development and configuration](60-operations/development-and-configuration.md)
- [Testing and production readiness](70-quality/testing-and-production-readiness.md)

### Future designs

- [Founding-partner entitlements](80-future/founding-partner-entitlements.md)
- [Future platform](80-future/future-platform.md)

### Visual assets

- [Screenshot register and capture rules](images/README.md)

## Visual policy

Mermaid diagrams are the primary visual because they stay reviewable in source control. Screenshots are included only when they teach something a flow diagram cannot. They must use demo data, contain no personal email, phone, address, token, or production identifier, and state the commit they represent. The old `docs/images/dashboard.png` is intentionally not copied here because it contains a real email address.
