# Context Ops (Mapping Tool Root)

This folder reduces context usage and unnecessary repo searching.

## What Is Manual

- `DOMAIN_MAP.md`: high-value map of where to look first.
- `WORKING_NOTES.md`: persistent decisions and exceptions.

## What Is Generated

Generated files live in `context/_generated/` — do not edit by hand.

| File | Purpose |
|------|---------|
| `SYMBOL_INDEX.md` | Classes, functions, routes per Python file |
| `DEPENDENCY_MAP.md` | Import graph per Python file |
| `FILE_INDEX.txt` | All tracked files (excludes data/caches) |
| `DIRECTORY_SUMMARY.md` | File counts by directory (3-level depth) |
| `MAPPING_RELATED_FILES.txt` | Files matching mapping/transaction keywords |
| `SEARCH_HOTSPOTS.md` | Key search areas with path validation |

## Commands

From `c:\Users\hp\Desktop\Omni\Mapping Tool`:

Regenerate all indices:
```powershell
powershell -ExecutionPolicy Bypass -File .\context\scripts\update-context.ps1
```

Force regenerate (ignores staleness check):
```powershell
powershell -ExecutionPolicy Bypass -File .\context\scripts\update-context.ps1 -Force
```

Search by scope:
```powershell
powershell -ExecutionPolicy Bypass -File .\context\scripts\search-context.ps1 -Pattern "transaction type" -Scope mapping
powershell -ExecutionPolicy Bypass -File .\context\scripts\search-context.ps1 -Pattern "PLMService" -Scope symbols
powershell -ExecutionPolicy Bypass -File .\context\scripts\search-context.ps1 -Pattern "plm_plugin" -Scope deps
powershell -ExecutionPolicy Bypass -File .\context\scripts\search-context.ps1 -Pattern "allocation" -Scope docs
```

Combined update + search:
```powershell
powershell -ExecutionPolicy Bypass -File .\context\scripts\prep-agent-context.ps1 -Pattern "transaction mapping" -Scope mapping
```

## Available Scopes

| Scope | Searches |
|-------|----------|
| `mapping` | docs/mapping, docs/api, backend/app/api |
| `backend` | entire backend/ |
| `docs` | docs/, backend/docs |
| `symbols` | SYMBOL_INDEX.md (classes, functions, routes) |
| `deps` | DEPENDENCY_MAP.md (import relationships) |
| `all` | entire repo |

## Suggested Routine

1. Run `update-context.ps1` once per day or before a focused work session (auto-skips if < 1h old).
2. Search `symbols` scope first for function/class lookups.
3. Search `deps` scope to trace import chains.
4. Search `mapping`/`docs`/`backend` for content searches.
5. Add only stable decisions to `WORKING_NOTES.md`.
