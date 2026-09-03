export type IdempotencyAttempt = {
  fingerprint: string;
  key: string;
};

export function requestAttempt(
  current: IdempotencyAttempt | null,
  fingerprint: string,
): IdempotencyAttempt {
  if (current?.fingerprint === fingerprint) return current;
  return { fingerprint, key: crypto.randomUUID() };
}

export function idempotencyHeaders(attempt: IdempotencyAttempt) {
  return { "Idempotency-Key": attempt.key };
}
