# Milestone 5 — The intelligence layer (plan, draft 2)

Chosen by the user (D079). Two capabilities: a **ranked worker feed** (M4) and the two **AI helpers that need no training data** — A1 (onboarding guidance + shift-post writing) and A6 (draft the offer message a manager sends). A2/A3/A4 (pilot-data AI) stay deferred.

Draft 2 folds in a code-grounded review (10 deltas, D081): the live slate moves to Redis, slate pages are re-filtered against live state, de-identification claims are corrected, ranking gains anti-feedback-loop controls, and the inference endpoint is locked down.

## Binding constraints (from the requirements, section 10 + compliance)

- **C4 / A7** — a suggestion is never an automated decision. Everything the ranker or assistant produces is presented to a person who accepts, edits, or ignores it; ranking and suggestion are permitted, automatic rejection/blocking/exclusion is not. Every ranking that affects a worker is explainable, appealable, and reviewable by a person.
- **A9 / near-zero cost** — the assistant runs deterministic/template logic by default, behind a provider interface, so no paid model call is required. The ranker is a deterministic signal model, not an ML model — zero inference cost, fully explainable.
- **A8 / L9** — personalization uses only data the venue owns or the worker consented to. The M4 profiling-consent event gates worker-personal ranking signals; without it the feed ranks on objective shift signals only.
- **L5** — objective matching criteria, non-discrimination (no protected-attribute *and no proxy* signals), an appeals path with a real reviewer, and a monitored outcome distribution.
- **A5** — suggestions and ranking prefer the venue's own team and pool before the market (the M5 relationship buckets already encode this; ranking refines within them).

## Security (binding — D080; controls ship with the feature)

Worker PII flows through assistant prompts and the ranker's per-worker slate, so these controls are built in, not bolted on. The structural backstop is C4 (human-in-the-loop) — nothing the AI produces is acted on automatically, bounding the blast radius of any hallucination, bad ranking, or injection to "a wrong draft a human catches."

- **Data residency.** Deterministic default and self-hosted Gemma keep prompt data on infra we control. The hosted-API provider is off by default.
- **De-identification at the provider boundary (and its limits).** The `AssistantProvider` contract takes a *de-identified* prompt: structured PII (names, rates, contact) is replaced with placeholders (`{worker}`, `{rate}`) before any model sees it, re-inserted into the draft client-side. **Caveat, stated honestly:** pseudonymized data is *still personal data* under GDPR (Recital 26), so de-id *reduces* — does not remove — the DPA/lawful-basis obligation on the hosted path. And placeholders cannot catch PII inside **free-text** (venue/shift notes, risk info). Therefore: **free-text is never sent to a hosted model** — the self-hosted path (data stays on our infra) is the only one that receives it. A hosted provider gets structured, de-identified fields only.
- **Inference-endpoint lockdown (OWASP LLM10/LLM06).** The self-hosted/serverless model endpoint has **no public ingress** — private network only, reachable solely by the app, with an app↔model auth token. Locking the app route is not enough; the model endpoint itself must not be internet-exposed.
- **Prompt-injection safety (LLM01/LLM02).** All user free-text is passed as delimited *data, never instructions*; system prompts are fixed and separated; an output-moderation pass screens drafts before the manager sees them; the human gate is the backstop. A pinned injection test (a note trying to override the system prompt or produce discriminatory copy) is part of Phase 2.
- **Non-discrimination (L5).** No protected-attribute or proxy signals in the ranker; the pinned test is a **proxy / outcome-distribution** check, not merely "no protected attribute present" (see ranker anti-feedback controls).
- **No prompt bodies in logs.** Audit records who invoked the assistant and when (existing event log), never prompt/response content.
- **Resilience (A9 "never forced").** Each model provider is wrapped in a **bounded timeout + circuit breaker**; on model failure or slowness the call degrades to the deterministic provider, so a down model never blocks shift posting or offering.
- **Model supply chain.** Self-hosted weights are digest-pinned with checksum verification; the serverless image is controlled.
- **Access & abuse.** Assistant endpoints are operator-authenticated, rate-limited, per-venue quota'd, timeout-bounded; the assistant only ever receives the caller's own tenancy-scoped data.
- **Slate & appeals isolation + retention.** The Redis slate and SQL appeals are tenancy-scoped — a worker reads only their own slate, and the explainability payload never exposes signals about other workers. The slate is per-worker PII: short Redis TTL is its retention; appeals follow the platform retention/erasure policy.

## Part A — Ranked feed (M4)

Turn M5's relationship-bucket ordering into a real ranking. The bucket order (your venues → pools → market) stays the coarse sort; ranking orders shifts **within** each bucket, replacing pure `start_time`.

- **Ephemeral slate in Redis, durable decision in the event log (revised — was a Postgres table).** On a fresh feed request (no cursor) the ranker scores the candidates and writes a **bounded ranked slate to Redis** — key `feedslate:{worker_id}:{fingerprint}`, value = ordered `shift_id`s + per-shift score/signals, **TTL ~10 min**, max ~200 items. Redis is already in the stack (token denylist, rate limiter). The slate is a short-lived pagination artifact — it does *not* belong in a migration-managed SQL table that would grow unbounded and need constant purging. The **durable** record needed for audit/measurement already exists: `shift.served` events carry `slate_id` + `position` in the append-only event log (`event_recorder.py`), so the ranking that produced any historical feed is reconstructable from the log, not a stored slate.
- **Slate fixes order; live state fixes inclusion (correctness).** Paginating by position must **re-filter each slate page against current visibility at read time** — still open, not filled, still reaches the worker (bucket predicates), not already applied/passed. A frozen slate otherwise serves shifts that were filled or cancelled between slate creation and the page read. Gone items are skipped (the page shrinks); when the slate is exhausted or expired, regenerate.
- **Cursor carries mode + slate identity (invalidation contract).** The signed cursor gains `mode` (`keyset` when ranking is off, `ranked` when on), `slate_id`, `position`, alongside the existing `filter_fingerprint`. Any mode / fingerprint / missing-slate mismatch → a fresh slate, never a silent wrong page. This extends the existing decode's fingerprint-rejection discipline; the deterministic keyset stays as the ranking-off fallback.
- **Deterministic signal ranker** (`services/feed_ranker.py`, pure + table-tested). Score = weighted sum of signals, each contributing an explainable reason:
  - pay attractiveness vs the worker's market median — *objective*
  - lead-time fit (how soon it starts) — *objective*
  - role fit (matches the worker's stated role) — *objective*
  - venue rating — *objective*
  - relationship familiarity (worked this venue before, how recently) — *personal, consent-gated, **weight-capped*** (see below)
  Weights are frozen, documented constants, tunable as data. No protected attributes or proxies.
- **Anti-feedback-loop / anti-proxy controls (L5).** A heavy familiarity signal entrenches — familiar workers keep surfacing, newcomers never do, which can *indirectly* disadvantage protected groups even with no protected attribute present. So: **cap the familiarity weight**, and **reserve a fraction of each page (exploration slots) for low-familiarity / newer shifts**. The L5 test checks the **outcome distribution** (are new/relationship-light shifts still surfaced?), not just signal absence.
- **Consent gate (L9).** Without profiling consent the personal familiarity signal is dropped and the ranker uses objective signals only; the response flags which mode produced it. `ConsentService.has_active_consent(user_id, "profiling")` is the gate.
- **Explainability + a real appeals path (A7).** Each ranked item carries a `ranking` payload: the top reasons in plain language ("Higher pay than most nearby", "You've worked here before", "Starts soon"). An **appeal** endpoint records a worker's objection (append-only, SQL) — and a **review surface** (`GET /system/feed-appeals` for platform staff, owner assigned) makes it genuinely reviewable by a person, as A7 requires. No automated re-decision; the appeal is a human-review request.
- **Boost placement composes on top** — a purchased boost still leads the market section within the ranked order (M1/M3 unchanged).
- **Migration 057: `feed_ranking_appeals` only** (append-only: appeal_id, worker_id, shift_id, slate_id, reason, created_at, plus review fields — reviewed_at, reviewed_by, outcome_note). No slate table.

## Part B — Assistant interface + A1 (onboarding + shift-post writing)

- **`AssistantProvider` interface** (`services/assistant/`) with a **`DeterministicAssistant` default**: template + venue-data logic, zero external calls, near-zero cost (A9). The contract takes a **de-identified structured** prompt (placeholders, not PII — free-text only travels to the self-hosted provider) and returns text a caller re-hydrates client-side. Each provider is wrapped in a **timeout + circuit breaker that falls back to deterministic** on failure. Config selects the provider; default is deterministic. Model, when enabled: **Gemma 3 12B** (Apache-2.0, on-hardware tested) — local via Ollama for dev, a serverless scale-to-zero GPU endpoint (Modal/RunPod/Baseten) with **private ingress** for production. A hosted API (Gemini Flash-Lite / GPT-5 mini) is an optional provider, off unless a DPA + no-train are in place, and it receives **structured de-identified fields only, never free-text**.
- **A1 onboarding helper** — `POST /assistant/onboarding` returns structured, prioritized setup guidance from the account's actual state (no venues, no team, no pay defaults, no shifts yet). Never blocks any flow — advice the manager can ignore.
- **A1 shift-post writing** — `POST /assistant/shift-post` takes structured inputs (role, location, timing, optional pay) and returns a polished description **plus a suggested pay range** from the venue's own fill history and market (reusing the I4 "what helps fill" signals). The manager edits and posts; the assistant never posts.
- Guardrails: outputs are drafts a human owns (C4); pay suggestions cite their basis (A7); uses only the venue's own data (A8).

## Part C — A6 (draft the offer message)

- **A6** — `POST /assistant/offer-message` drafts the message a manager sends when offering a shift to a named worker, from the shift + worker + venue data. **Point in the flow:** manager-initiated, *before* sending — the manager opens the named-offer action, taps "suggest a message", edits the draft, and sends it themselves. The assistant **never sends** it (C4 / Q8 unsettled). The existing hardcoded offer/notify copy in `escalation_service` stays as the automatic-system message; A6 is only for the manager's own outreach.
- Wire the "suggest a message" action into the named-offer path so the draft is one tap away, editable before send.

## Part D — Clients (minimal, D075)

- Feed: a small "why" line under ranked items (the top reason), and a consent nudge if profiling is off ("Turn on personalized suggestions").
- Console: a "Help me write this" action on the shift form (fills description + pay from A1); an onboarding checklist card from A1; a "suggest a message" button on the named-offer flow (A6 draft, editable).
- No revamp — functional surfaces only; the full redesign is the separate deferred milestone.

## Phases (each leaves both suites green; migrations up-down-up on both engines)

1. **Ranker + slate** — `feed_ranker` (pure, table-tested incl. the L5 outcome test), Redis slate + TTL, live-state re-filter on each page, cursor mode/slate-id + invalidation, consent gate, explainability, appeals endpoint + review surface, migration 057 (`feed_ranking_appeals`). Ranking-on uses the slate; keyset stays the ranking-off fallback.
2. **Assistant interface + A1** — provider interface with timeout/circuit-breaker/deterministic fallback, de-id boundary (structured placeholders; free-text kept off hosted), onboarding + shift-post endpoints, pay suggestion from I4, the pinned injection + moderation tests, inference-endpoint auth.
3. **A6** — offer-message draft endpoint + named-offer wiring (draft-before-send).
4. **Clients** — the minimal surfaces above; web tsc+build, mobile tsc.
5. **Close** — Docker rebuild, live e2e (ranked feed with reasons + consent on/off + a stale-item skip + exploration slot, a written shift post, a drafted offer message, a model-down deterministic fallback), acceptance report.

## Split (Fable ∥ Codex, D074 loop)

- **Codex**: Part A ranker + Redis slate + cursor-mode change + migration 057 (the delicate pagination/invalidation work).
- **Fable**: assistant interface + A1 + A6 (greenfield), client surfaces, the integration gate, review of Codex's Part A.
- Standing rules unchanged: shared checkout, stage by explicit path, both legs + zero PG skips per phase, frozen migration literals, no comments, no default fallbacks, push only on explicit confirmation.

## Deferred / open

A2 (pricing predictor), A3 (shift-fill targeting), A4 (suggested workers) — need pilot data. Whether A6 may ever auto-send (Q8) — stays no until settled. Enterprise model quality (if a small open model proves insufficient on some task) — swap the provider, interface unchanged. Independent cross-check of this revised plan by Codex is optional (its quota returns 5:20 PM); the 10 review deltas above are already folded in.
