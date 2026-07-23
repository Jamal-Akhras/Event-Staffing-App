# Legal Review Checklist

Send this list and `apps/web/src/pages/LegalPage.tsx` to the reviewing lawyer.
Every bracketed token below appears at least once in the legal pages and must be replaced.

## Placeholders to fill

| Token | Where it appears | Notes |
|---|---|---|
| `[LEGAL ENTITY NAME]` | Terms §1, Privacy §1 | The contracting entity. UK Ltd / FZ-LLC / other. |
| `[REGISTERED ADDRESS]` | Terms §1, Privacy §1 | Registered office address shown on Companies House / equivalent. |
| `[SUPPORT EMAIL]` | Terms §1 | Customer support inbox. |
| `[PRIVACY CONTACT EMAIL]` | Terms §1, Privacy §1, Privacy §6 | DPO or privacy contact. Often `privacy@<domain>`. |
| `[DPO OR REPRESENTATIVE CONTACT]` | Privacy §1 | UK GDPR Art. 27 representative if no UK establishment, or appointed DPO. |
| `[SUBPROCESSOR LIST URL]` | Privacy §4 | Link to `docs/legal/subprocessors.md` once published, or a public URL. |
| `[ANALYTICS PROVIDERS]` | Cookies §2 | List analytics products if/when enabled. |
| `[RETENTION PERIOD]` | Runbook backups | Days/months for DB and uploads retention. |
| `[OWNER NAME]` / `[ON-CALL PHONE OR SLACK]` / `[CLOUD OWNER]` / `[BACKUP OWNER]` | Runbook | Operational ownership. Not customer-facing but required for incident response. |

## Items the lawyer should review or draft

- Confirm jurisdiction and governing law clauses for both UK and UAE entities. Today the docs reference UK GDPR + UAE PDPL but make no governing-law choice.
- Confirm dispute resolution (arbitration vs courts) and venue.
- Confirm consumer protection language for workers (B2C exposure) and B2B terms for operators.
- Draft Data Processing Agreement (DPA) template using the EU Commission's Standard Contractual Clauses 2021 or UK IDTA where applicable. Reference it from Privacy §4.
- Confirm whether marketing emails will be sent. If yes, add opt-in mechanics and add a marketing-cookie section.
- Confirm cookie banner requirement. Today only strictly-necessary and error-reporting (Sentry) cookies are used; if analytics is added, a consent banner becomes required in the UK and most EU markets.
- Confirm payment terms once Stripe (UK) and Telr (UAE) integrations land. Add fee schedule and refund/chargeback policy.
- Confirm employer/worker classification language. Current Terms §2 declares Venue OS is software, not employer/agency. A UK employment lawyer should confirm this position holds under the Worker Protection Act and supply-of-services rules.

## Versioning

- Each policy carries its own `updated` date in `apps/web/src/pages/LegalPage.tsx`. Bump only the doc that changed.
- Material changes require user re-acceptance. Plan a "Re-accept updated terms" modal before the next major change.

## Sign-off

- [ ] Lawyer reviewed Terms
- [ ] Lawyer reviewed Privacy Policy
- [ ] Lawyer reviewed Cookie Policy
- [ ] DPA template drafted
- [ ] Subprocessor list published
- [ ] All bracketed placeholders removed from `LegalPage.tsx` and `RUNBOOK.md`
