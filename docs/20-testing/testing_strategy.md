
# Testing Strategy (Mandatory)

Testing exists to ENFORCE correctness, not to improve coverage numbers.

## Test Layers

### 1. Domain Tests (Highest Priority)
Location: packages/domain/tests
- Test every state transition
- Test invalid transitions
- Test idempotency
- Test invariants

### 2. API Tests
Location: apps/api/tests
- Endpoint → state mapping
- Permission enforcement
- Error codes

### 3. Integration Tests
- Booking → payment flow
- No-show sweeps
- Cancellation penalties

## Rules
- No feature without tests
- No test mocking the domain layer
- Domain tests must run without FastAPI
