# Agent Workflow (Mapping Tool Root)

This repository uses a context-first workflow to reduce token usage and broad code searching.

## Important Rules

- Build modular first. Think ahead: keep entrypoints stable and isolate logic into cohesive modules from the start.
- Prefer handwritten production files below 400 lines.
- Files above 500 lines require a cohesion/responsibility review.
- Handwritten production files may not exceed 800 lines without an explicit documented exception.
- Tests may reach 1,000 lines when they cover one coherent subsystem.
- Generated files, migrations, declarative schemas and data fixtures are exempt.
- Never split a cohesive module solely to satisfy a line count.
- Prefer functions below roughly 60 lines and components/services with one clear responsibility.
- Do not add default fallbacks during development. If something fails, let it fail.
- Do not leave empty try/catch blocks.
- Do not reinvent the wheel. Prefer open source, self-hosted libraries when appropriate. Ask the user to confirm library choice.
- Design UI for the end-user, not for the schema.
- Before starting a task, develop a plan by working backwards from the goal to the steps and actions required.

## Code Style

- Avoid comments unless absolutely required by a non-obvious workaround or unavoidable complexity.
- Use clear, descriptive variable and function names.
- If code needs comments to be understood, refactor first.

## Continuity Ledger (Compaction Safe)

Maintain a single continuity file for this workspace: `CONTINUITY.md`.
`CONTINUITY.md` is the canonical briefing designed to survive compaction.

### Operating Rule

- At the start of each assistant turn, read `CONTINUITY.md` before acting.
- Update `CONTINUITY.md` only when there is a meaningful delta in:
  - Goal/success criteria
  - Invariants/constraints
  - Decisions
  - State (Done/Now/Next)
  - Open questions
  - Working set
  - Important tool outcomes

### Keep It Bounded

- Keep `CONTINUITY.md` short and high signal:
  - `Snapshot`: <= 25 lines
  - `Done (recent)`: <= 7 bullets
  - `Working set`: <= 12 paths
  - `Receipts`: keep last 10-20 entries
- If sections exceed caps, compress older items into milestone bullets with pointers.
- Do not paste raw logs.

### Anti-Drift Rules

- Facts only, no transcripts.
- Every entry must include:
  - Date or ISO timestamp
  - Provenance tag: `[USER]`, `[CODE]`, `[TOOL]`, `[ASSUMPTION]`
- If unknown, write `UNCONFIRMED`.
- If something changes, supersede it explicitly.

### Decisions And Incidents

- Record durable choices in `Decisions` as ADR-lite entries, for example: `D001 ACTIVE: ...`.
- For recurring issues, use incident capsules with:
  - Symptoms
  - Evidence pointers
  - Mitigation
  - Status

### Plan Tool Vs Ledger

- Use short execution plans for immediate steps.
- Use `CONTINUITY.md` for long-running continuity, not micro task lists.
- Keep short-term plans and ledger consistent at intent/progress level.

### In Replies

- Start with a brief `Ledger Snapshot`:
  - Goal
  - Now
  - Next
  - Open Questions
- Print full ledger only when it materially changed or when requested.

## Default Behavior (Required)

Before exploring files for any non-trivial task:

1. Run context update (auto-skips if < 1h old):
```powershell
powershell -ExecutionPolicy Bypass -File .\context\scripts\update-context.ps1
```
2. Search symbols first to find the right function/class:
```powershell
powershell -ExecutionPolicy Bypass -File .\context\scripts\search-context.ps1 -Pattern "<function or class name>" -Scope symbols
```
3. Trace dependencies if needed:
```powershell
powershell -ExecutionPolicy Bypass -File .\context\scripts\search-context.ps1 -Pattern "<module name>" -Scope deps
```
4. Fall back to content search for broader exploration:
```powershell
powershell -ExecutionPolicy Bypass -File .\context\scripts\search-context.ps1 -Pattern "<task keywords>" -Scope mapping
```
5. Start investigation using:
- `context/DOMAIN_MAP.md`
- `context/_generated/SYMBOL_INDEX.md`
- `context/_generated/DEPENDENCY_MAP.md`

## Search Scopes

| Scope | Searches | Use When |
|-------|----------|----------|
| `symbols` | SYMBOL_INDEX.md | Finding functions, classes, routes |
| `deps` | DEPENDENCY_MAP.md | Tracing imports and call chains |
| `mapping` | docs/mapping, docs/api, backend/app/api | Mapping decisions and API specs |
| `backend` | entire backend/ | Implementation details |
| `docs` | docs/, backend/docs | Documentation and specs |
| `all` | entire repo | Last resort |

## Search Priorities

1. `symbols` scope — find the exact function/class/route
2. `deps` scope — trace what imports what
3. `mapping` scope — content search within mapping-related files
4. Open smallest relevant files first
5. Expand to `backend` or `all` only with explicit reason

## Scope Rules

- First-pass scope must be limited to:
  - `docs/mapping/`
  - `docs/api/`
  - `maxim-pipeline-studio/backend/app/api/`
- Only expand beyond first-pass scope if scoped search is insufficient.
- Do not run repo-wide broad scans until scoped paths are checked.

## Persistence Rules

- Write only stable decisions to `context/WORKING_NOTES.md`.
- Do not manually edit files under `context/_generated/`.

## Quick Commands

```powershell
powershell -ExecutionPolicy Bypass -File .\context\scripts\search-context.ps1 -Pattern "build_transactions" -Scope symbols
```

```powershell
powershell -ExecutionPolicy Bypass -File .\context\scripts\search-context.ps1 -Pattern "plm_plugin" -Scope deps
```

```powershell
powershell -ExecutionPolicy Bypass -File .\context\scripts\search-context.ps1 -Pattern "transaction type" -Scope mapping
```
