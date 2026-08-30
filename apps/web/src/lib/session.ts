const SESSION_KEY = "venueos.sessionId";

export function sessionId() {
  const existing = window.sessionStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const created = crypto.randomUUID();
  window.sessionStorage.setItem(SESSION_KEY, created);
  return created;
}

export const appVersion = import.meta.env.VITE_APP_VERSION;
