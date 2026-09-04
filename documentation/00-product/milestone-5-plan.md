# Milestone 5 — The intelligence layer (plan, draft 1)

Chosen by the user (D079). Two capabilities: a **ranked worker feed** (M4) and the two **AI helpers that need no training data** — A1 (onboarding guidance + shift-post writing) and A6 (draft the offer message a manager sends). A2/A3/A4 (pilot-data AI) stay deferred.

## Binding constraints (from the requirements, section 10 + compliance)

- **C4 / A7** — a suggestion is never an automated decision. Everything the ranker or assistant produces is presented to a person who accepts, edits, or ignores it; ranking and suggestion are permitted, automatic rejection/blocking/exclusion is not. Every ranking that affects a worker is explainable, appealable, and reviewable by a person.
- **A9 / near-zero cost** — the assistant runs deterministic/template logic by default, behind a provider interface, so no paid model call is required and a self-hosted model can be swapped in later. No external LLM is wired as the default. The ranker is a deterministic signal model, not an ML model — zero inference cost, fully explainable.
- **A8 / L9** — personalization uses only data the venue owns or the worker consented to. The profiling-consent event added in M4 gates worker-personal ranking signals; without it the feed ranks on objective shift signals only.
- **L5** — objective matching criteria, non-discrimination (no protected-attribute or proxy signals), and an appeals hook on ranking output.
- **A5** — suggestions and ranking prefer the venue's own team and pool before the market (the M5 relationship buckets already encode this; ranking refines within them).

## Security (binding — user made this a priority for the AI layer, D080)

Worker PII flows through assistant prompts and the ranker's per-worker slate, so these controls ship with the feature, not after. The structural backstop is C4 (human-in-the-loop) — nothing the AI produces is acted on automatically, which bounds the blast radius of any hallucination, bad ranking, or injection to "a wrong draft a human catches."

- **Data residency.** Deterministic default and self-hosted Gemma keep prompt data on infra we control; PII never crosses a trust boundary. The hosted-API provider is off by default.
- **De-identification at the provider boundary.** The `AssistantProvider` contract takes a *de-identified* prompt: real names/rates/contact are replaced with placeholders (`{worker}`, `{rate}`) before the model sees anything, and re-inserted into the draft client-side. A model — self-hosted or hosted — never receives raw PII. This is a hard interface rule, not an option.
- **Prompt-injection safety.** All user free-text (venue/shift notes, names) is passed as delimited *data, never instructions*; system prompts are fixed and separated; an output-moderation pass screens drafts before they reach the manager; the human gate is the backstop. A pinned injection test (a note that tries to override the system prompt / produce discriminatory copy) is part of Phase 2.
- **Non-discrimination (L5).** No protected-attribute or proxy signals in the ranker; a pinned non-discrimination test on both ranker and assistant output.
- **No prompt bodies in logs.** Audit records who invoked the assistant and when (existing event log), never the prompt/response content. Retention follows the platform policy.
- **Model supply chain.** Self-hosted weights are version-pinned with checksum verification; the serverless image is controlled.
- **Access & abuse.** Assistant endpoints are operator-authenticated, rate-limited, per-venue quota'd, and timeout-bounded; the assistant only ever receives the caller's own tenancy-scoped data.
- **Ranker slate isolation.** The persisted slate and appeals data carry the same tenancy scoping as everything else — a worker reads only their own slate, and the explainability payload never exposes signals about other workers.

## Part A — Ranked feed (M4)

Turn M5's relationship-bucket ordering into a real ranking. The bucket order (your venues → pools → market) stays as the coarse sort; ranking orders shifts **within** each bucket, replacing pure `start_time`. `slate_id` already exists on feed responses (D065, built so "the ranking that produced a list can be reconstructed later") — this is the materialized-slate design it was built for.

- **Materialized ranked slate.** On a fresh feed request (no cursor) the service scores the candidate shifts and persists a bounded ranked slate (`ranked_feed_slates`: slate_id, worker_id, market_id, filter_fingerprint, ordered shift_ids + per-shift score/signals, created_at, expiry). Pagination reads the frozen slate by position — true global ranking with complete, stable pagination (the keyset cursor becomes a position into the slate). A stale/absent slate (filters changed, expired) triggers a fresh slate. This replaces the keyset cursor for ranked mode; the deterministic keyset stays as the fallback when ranking is off.
- **Deterministic signal ranker** (`services/feed_ranker.py`, pure + table-tested). Score = weighted sum of objective signals, each contributing an explainable reason:
  - relationship strength / familiarity (worked this venue before, how recently) — *personal, consent-gated*
  - pay attractiveness vs the worker's market median — *objective*
  - lead-time fit (how soon it starts) — *objective*
  - role fit (matches the worker's stated role) — *objective*
  - venue rating / reliability of the offer — *objective*
  No protected attributes or proxies (L5). Weights are frozen constants, documented, tunable as data.
- **Consent gate (L9).** If the worker has not granted profiling consent, personal signals are dropped and the ranker uses objective signals only; the response says so. `ConsentService.has_active_consent(user_id, "profiling")` (already built) is the gate.
- **Explainability (A7).** Each ranked item carries a `ranking` payload: the top contributing reasons in plain language ("Higher pay than most nearby", "You've worked here before", "Starts soon"). An **appeal/feedback** endpoint records a worker's objection to how a shift was ranked (append-only, human-reviewable) — satisfies A7/L5 without any automated re-decision.
- **Boost placement composes on top** — a purchased boost still leads the market section within the ranked order (M1/M3 unchanged).
- **Measurement** already exists (D065 slate_id/position on feed events); the persisted slate makes `position` meaningful and reconstructable.
- Migration 057: `ranked_feed_slates` (+ its items) and `feed_ranking_appeals`.

## Part B — Assistant interface + A1 (onboarding + shift-post writing)

- **`AssistantProvider` interface** (`services/assistant/`) with a **`DeterministicAssistant` default**: template + venue-data logic, zero external calls, near-zero cost (A9). The contract takes a **de-identified** prompt (placeholders, not PII — see Security) and returns text a caller re-hydrates client-side, so no provider ever sees raw worker data. A config flag selects the provider; default is deterministic. The model choice, when a provider is enabled, is **Gemma 3 12B** (Apache-2.0, on-hardware tested good enough for A1/A6) — local via Ollama for dev, a serverless scale-to-zero GPU endpoint (Modal/RunPod/Baseten) for production, never a dedicated always-on box or a dev PC. A hosted API (Gemini Flash-Lite / GPT-5 mini) is a further optional provider, off unless a DPA + no-train + de-identification are all in place.
- **A1 onboarding helper** — `POST /assistant/onboarding` returns structured, prioritized setup guidance derived from the account's actual state (no venues, no team, no pay defaults, no shifts posted yet, etc.). Never blocks any flow (the "never forced" condition) — it is advice the manager can ignore.
- **A1 shift-post writing** — `POST /assistant/shift-post` takes structured inputs (role, location, timing, optional pay) and returns a polished description **plus a suggested pay range** computed from the venue's own fill history and the market (reusing the I4 "what helps fill" signals). The manager edits and posts; the assistant never posts.
- Guardrails: outputs are drafts a human owns (C4); pay suggestions cite their basis (A7); uses only the venue's own data (A8).

## Part C — A6 (draft the offer message)

- **A6** — `POST /assistant/offer-message` drafts the message a manager sends when offering a shift to a named worker, from the shift + worker + venue data. The manager reviews, edits, and sends; the assistant **never sends** it (C4 / open question Q8 — sending on the manager's behalf is explicitly not settled). The existing hardcoded offer/notify copy in `escalation_service` stays as the automatic-system message; A6 is for the manager-initiated named offer.
- Wire a "suggest a message" action into the named-offer path so the draft is one tap away, editable before send.

## Part D — Clients (minimal, D075)

- Feed: a small "why" line under ranked items (the top reason), and a consent nudge if profiling is off ("Turn on personalized suggestions").
- Console: a "Help me write this" action on the shift form (fills description + pay from A1); an onboarding checklist card from A1; a "suggest a message" button on the named-offer flow (A6 draft, editable).
- No revamp — functional surfaces only; the full redesign is the separate deferred milestone.

## Phases (each leaves both suites green, migrations up-down-up on both engines)

1. **Ranker + slate** — `feed_ranker` (pure, table-tested), `ranked_feed_slates` (migration 057), slate persistence + pagination, consent gate, explainability payload, appeals endpoint. Feed switches to slate mode when ranking is on; keyset fallback preserved.
2. **Assistant interface + A1** — provider interface, deterministic default, onboarding + shift-post endpoints, pay-suggestion from I4 signals.
3. **A6** — offer-message draft endpoint + named-offer wiring.
4. **Clients** — the minimal surfaces above; web tsc+build, mobile tsc.
5. **Close** — Docker rebuild, live e2e (ranked feed with reasons + consent on/off, a written shift post, a drafted offer message), acceptance report.

## Split (Fable ∥ Codex, D074 loop)

- **Codex**: Part A ranker + slate (the meaty keyset→slate migration and pagination change), migration 057.
- **Fable**: assistant interface + A1 + A6 (greenfield, template-heavy), client surfaces, the integration gate, review of Codex's Part A.
- Standing rules unchanged: shared checkout, stage by explicit path, both legs + zero PG skips per phase, frozen migration literals, no comments, no default fallbacks, push only on explicit confirmation.

## Deferred / open

A2 (pricing predictor), A3 (shift-fill targeting), A4 (suggested workers) — need pilot data. Whether A6 may ever auto-send (Q8) — stays no until settled. The self-hosted model choice (Q9) — the interface makes it swappable; the default ships without it. Protected-attribute audit of the ranker signals — include an explicit non-discrimination test in Phase 1.
