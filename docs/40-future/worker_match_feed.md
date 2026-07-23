# Worker Match Feed

## Status
- Date: 2026-05-03
- Status: Initial mobile UI slice implemented; algorithmic ranking and gesture-native swipe remain future work.

## Concept
The worker shift search experience can evolve into a feed-first discovery surface:

- A vertical, Instagram-like feed remains the primary browsing pattern so workers can compare roles, pay, time, location, and requirements without losing context.
- Swipe shortcuts can be added for high-frequency decisions: swipe right to quick apply, swipe left to pass.
- The app should avoid a pure Tinder-style deck as the only interface because shift decisions are detail-heavy and workers may need to compare options by date, travel, pay, and role fit.

## Current Mobile Slice
- Browse now uses a vertical feed of ranked open shifts.
- Each shift exposes direct Pass, Details, and Quick apply actions.
- Pass is persisted per worker through `/workers/{worker_id}/feed-state`.
- Undo restores the most recently passed shift back into the feed.
- Quick apply submits a default application message immediately.
- Details still supports a custom message before applying.

## UX Guardrails
- Keep tap-to-open details, filters, search, and list browsing available.
- Make swipe actions reversible with undo.
- Show the critical decision data before any action: role, venue/location, start time, duration, pay, workers needed, reliability requirements, notes, and commute/travel context when available.
- Do not make passed shifts unrecoverable; workers need a clear undo/reset path.
- Keep accessibility paths for users who cannot or do not want to use gestures.

## Ranking Signals For Later
Initial algorithmic ranking should start explainable and conservative:

- Date and timing preference, including weekend vs weekday behavior.
- Distance/location fit and repeated venues.
- Work type/role match.
- Pay rate and shift duration.
- Worker availability and existing bookings.
- Prior applications, approvals, cancellations, no-shows, and reliability fit.

## Product Position
Algorithmic ranking should still be treated as an optimization layer after the core browse/apply/check-in workflow is stable. The current priority is keeping the worker mobile flow operational while improving the feed UI in small, testable slices.
