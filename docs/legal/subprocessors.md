# Subprocessors

This list is referenced from the Privacy Policy as `[SUBPROCESSOR LIST URL]`.
Publish a stable URL once the production stack is locked.

## Active subprocessors

| Vendor | Purpose | Personal data | Location | Transfer mechanism |
|---|---|---|---|---|
| `[POSTGRES HOST]` | Primary database | Account, marketplace, booking, message records | `[REGION]` | `[SCC / UK IDTA / N/A]` |
| `[FILE STORAGE]` | Uploads (avatars, venue photos) | Uploaded images and filenames | `[REGION]` | `[SCC / UK IDTA / N/A]` |
| Sentry | Error reporting | Stack traces, request paths, browser/device metadata | EU or US tenant | SCC or DPF, depending on tenant |
| `[EMAIL PROVIDER]` | Transactional email (reset password, alerts) | Email address, message body, delivery status | `[REGION]` | `[SCC / UK IDTA / N/A]` |

## Pending evaluation

- Payments: Stripe (UK), Telr (UAE). Will be added when payment endpoints ship.
- Analytics: deferred. Not added until a consent banner ships.

## Change log

- 2026-05-25: Initial draft.
