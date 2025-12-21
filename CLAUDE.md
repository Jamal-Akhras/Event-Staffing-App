
# Claude Instructions (Authoritative)

You are building an MVP for a reliability-first on-demand event staffing platform.

## Core Engineering Principles (NON-NEGOTIABLE)

### KISS (Keep It Simple, Stupid)
- Prefer the simplest solution that satisfies the spec.
- Avoid clever abstractions.
- Readability > flexibility.

### YAGNI (You Aren’t Gonna Need It)
- Do NOT add speculative features.
- Do NOT generalise for future use cases.
- Only implement what is explicitly required by the spec.

### SOLID
- Single Responsibility: one reason to change per module.
- Open/Closed: extend via composition, not modification.
- Liskov Substitution: no surprising behaviour.
- Interface Segregation: small, focused interfaces.
- Dependency Inversion: depend on abstractions, not concretes.

## Source of Truth
1. docs/00-idea/idea.md
2. docs/10-specs/state_machine_spec.md
3. docs/20-testing/testing_strategy.md
4. docs/30-delivery/STATUS.md

## Documentation Discipline (MANDATORY)
After every meaningful change:
- Update README.md (high-level status)
- Update docs/30-delivery/STATUS.md
- Append to docs/30-delivery/DEVLOG.md

Failure to update docs is a bug.

## Architecture Rules
- Backend: FastAPI, modular monolith
- Frontend: React (web), thin UI
- Domain logic lives in packages/domain
- UI must not contain business rules
- All state transitions must be validated and tested
