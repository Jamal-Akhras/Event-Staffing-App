# Endpoint Reference

This is a human-readable inventory of routes mounted by `apps/api/src/main.py`. Request/response field definitions remain authoritative in the Pydantic schemas and development OpenAPI output.

Legend: **Public** requires no session; **Worker** and **Operator** require that role; **Participant** means the worker or venue connected to the underlying record; **System** is an internal actor. “Verified” means production also requires email verification.

## Health and markets

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/health` | Public | Shallow liveness alias |
| GET | `/live` | Public | Shallow process liveness |
| GET | `/ready` | Public/platform | Database/Redis readiness plus outbox/worker detail |
| GET | `/markets` | Public | List active launch markets and currency/timezone configuration |

## Authentication and account lifecycle

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/auth/register` | Public | Register worker and profile |
| POST | `/auth/register/operator` | Public + invite | Register organisation, venue and owner |
| POST | `/auth/login` | Public | Issue bearer session |
| GET | `/auth/me` | Authenticated | Return actor, tenant and auth mode |
| POST | `/auth/logout` | Authenticated | Revoke current token |
| POST | `/auth/logout-all` | Authenticated | Revoke all sessions through version increment |
| POST | `/auth/forgot-password` | Public | Request password reset |
| POST | `/auth/reset-password` | Public + token | Set new password |
| POST | `/auth/verify-email` | Public + token | Mark email verified |
| POST | `/auth/resend-verification` | Public | Reissue verification email without account enumeration |
| POST | `/auth/account-export` | Authenticated + password | Export account data |
| DELETE | `/auth/account` | Authenticated + password | Deactivate and anonymise account |

## Organisation, venue and account profile

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/organisations/me` | Operator | Read current organisation |
| GET | `/venues` | Operator | List venues in current organisation |
| GET | `/accounts/me` | Operator | Read active venue profile (compatibility name) |
| GET | `/venues/me` | Operator | Read active venue profile |
| PUT | `/accounts/me` | Operator | Update active venue profile (compatibility name) |
| PUT | `/venues/me` | Operator | Update active venue profile |

There are no mounted membership-management, venue-creation or active-venue switching endpoints yet.

## Shifts and templates

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/shifts` | Operator | Create shift; supports `Idempotency-Key` |
| GET | `/shifts` | Worker/Operator | List visible/scoped shifts |
| GET | `/shifts/{shift_id}` | Worker/Operator | Read an open worker-visible or owned venue shift |
| POST | `/shifts/{shift_id}/clone` | Operator | Clone owned shift |
| PUT | `/shifts/{shift_id}` | Operator | Update safe terms/capacity |
| POST | `/shifts/{shift_id}/close` | Operator | Stop applications, preserve bookings |
| POST | `/shifts/{shift_id}/cancel` | Operator | Cancel pre-start shift with reason |
| POST | `/templates` | Operator | Create template |
| GET | `/templates` | Operator | List venue templates |
| GET | `/templates/{template_id}` | Operator | Read template |
| PUT | `/templates/{template_id}` | Operator | Update template |
| DELETE | `/templates/{template_id}` | Operator | Delete template |
| POST | `/templates/{template_id}/generate` | Operator | Generate shifts for a range |

## Discovery and worker profiles

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/workers/me/feed` | Worker | Cursor-paginated market feed |
| GET | `/workers/{worker_id}/feed-state` | Worker self | List passed shifts |
| PUT | `/workers/{worker_id}/feed-state/{shift_id}` | Worker self | Save pass state |
| DELETE | `/workers/{worker_id}/feed-state/{shift_id}` | Worker self | Restore passed shift |
| GET | `/workers` | Operator | List venue-relevant workers |
| GET | `/workers/{worker_id}` | Operator or worker self | Read profile at allowed visibility |
| PUT | `/workers/{worker_id}` | Worker self | Update profile |
| GET | `/workers/{worker_id}/earnings` | Worker self | Summarize booking earnings |

## Applications

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/applications` | Verified worker self | Apply once; supports `Idempotency-Key` |
| GET | `/applications` | Worker/Operator | List caller-scoped applications |
| POST | `/applications/{application_id}/approve` | Operator | Approve and atomically create booking |
| POST | `/applications/{application_id}/reject` | Operator | Reject pending application |
| POST | `/applications/{application_id}/withdraw` | Worker self | Withdraw before shift start with reason |
| PUT | `/applications/{application_id}/message` | Participant | Edit pending application message |
| GET | `/applications/{application_id}/message-history` | Participant | Read previous application messages |

## Bookings and attendance

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/bookings` | Worker/Operator | List caller-scoped bookings |
| GET | `/bookings/{booking_id}` | Participant | Read booking |
| POST | `/bookings/{booking_id}/confirm` | Operator | Requested → confirmed |
| POST | `/bookings/{booking_id}/check-in` | Worker | Confirmed → checked in |
| POST | `/bookings/{booking_id}/check-out` | Worker | Checked in → checked out |
| POST | `/bookings/{booking_id}/approve` | Operator | Checked out → approved |
| POST | `/bookings/{booking_id}/record-payment` | Operator | Record external payment and mark paid |
| POST | `/bookings/{booking_id}/pay` | Operator | Compatibility alias for record-payment |
| POST | `/bookings/{booking_id}/no-show` | Operator/System | Confirmed → no-show |
| POST | `/bookings/{booking_id}/cancel/worker` | Worker | Cancel own requested/confirmed booking |
| POST | `/bookings/{booking_id}/cancel/operator` | Operator | Cancel venue booking |
| POST | `/system/no-show-sweep` | System | Process expired confirmations |

## Messages and notifications

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/shifts/{shift_id}/messages` | Verified participant | Send contextual message; idempotent retry supported |
| GET | `/shifts/{shift_id}/messages` | Participant | Read contextual thread |
| POST | `/messages/{message_id}/read` | Participant | Mark message read |
| GET | `/notifications` | Authenticated | Cursor-paginated actor inbox |
| POST | `/notifications/{notification_id}/read` | Owner | Mark one notification read |
| POST | `/notifications/read-all` | Authenticated | Mark actor inbox read |
| GET | `/notification-preferences` | Authenticated | Read category/channel preferences |
| PUT | `/notification-preferences` | Authenticated | Update preferences |
| POST | `/devices/push-tokens` | Authenticated | Register/update native device token |
| DELETE | `/devices/push-tokens/{push_token_id}` | Owner | Revoke native device token |
| GET | `/workers/{worker_id}/notifications` | Worker self | Legacy worker inbox |
| POST | `/workers/{worker_id}/notifications/read-all` | Worker self | Legacy read-all |

## Ratings and reports

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/bookings/{booking_id}/rate` | Verified participant | Create one bilateral rating |
| GET | `/ratings/pending` | Worker/Operator | List eligible unrated bookings |
| GET | `/workers/{worker_id}/rating-summary` | Operator | Read worker rating summary |
| GET | `/venues/{venue_id}/rating-summary` | Worker/Operator | Read venue rating summary |
| GET | `/accounts/me/completed-shifts` | Operator | List completed shifts for rating UI |
| POST | `/reports` | Verified Worker/Operator | Submit safety/trust report |
| GET | `/reports/me` | Worker/Operator | List caller's reports |
| GET | `/system/reports` | System | List reports for review |
| PATCH | `/system/reports/{report_id}` | System | Update report status/resolution |

## Uploads

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/uploads/avatar` | Verified worker | Upload processed worker avatar |
| POST | `/uploads/venue-photo` | Verified operator | Upload venue gallery image |
| POST | `/uploads/venue-avatar` | Verified operator | Upload venue avatar |

## Not mounted

`POST /payments/quote` exists in source but its router is not included by `main.py`. It must not be presented to clients or partners as a supported endpoint.
