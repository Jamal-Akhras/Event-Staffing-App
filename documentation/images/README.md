# Visual Asset Register

This folder is the controlled home for screenshots used by the documentation.

## Current status

No screenshot is approved at this revision. The existing `docs/images/dashboard.png` contains a real email address. Two automated redaction attempts removed that address but changed unrelated UI text, so they were discarded rather than presented as faithful screenshots.

The 42 Mermaid diagrams elsewhere in this library are current and source-controlled. Screenshots should be added during final UI QA, when the real web and release-build mobile clients can be captured with synthetic data.

## Required capture set

| Filename | Surface | What it should explain |
|---|---|---|
| `web-public-home.png` | Web home | Product proposition and route to each audience |
| `web-venue-dashboard.png` | Protected venue web | Coverage, attention queue and common actions |
| `web-application-review.png` | Protected venue web | Applicant comparison and decision workflow |
| `mobile-worker-feed.png` | Mobile browse | Shift card, filters and market context |
| `mobile-worker-map.png` | Mobile browse map | Geographic discovery |
| `mobile-booking.png` | Mobile shifts | Attendance, cancellation and messaging actions |
| `mobile-notification-rating.png` | Mobile alerts/rating | Entity navigation and bilateral trust loop |

## Capture rules

- Use blank/demo accounts and synthetic marketplace data.
- Show no real email, phone, address, name, push token, payment reference or internal identifier.
- Capture the exact committed UI; do not use AI-generated replacements as product screenshots.
- Prefer PNG at the native viewport/device resolution.
- Record client, route/screen, viewport/device, commit and capture date in the caption.
- Re-capture when a material layout or flow changes; remove obsolete images rather than keeping unlabeled history.

## Caption template

```text
Venue dashboard — React web, /app, 1440×900, synthetic data, commit <sha>, captured <date>.
```
