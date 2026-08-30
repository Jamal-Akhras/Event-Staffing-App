import { API_BASE, getAuthHeaders } from "./api";

const FLUSH_INTERVAL_MS = 5000;
const MAX_BATCH = 25;

export type TrackedEvent = {
  name: string;
  subject_type?: string;
  subject_id?: string;
  context?: Record<string, unknown>;
  occurred_at: string;
};

let queue: TrackedEvent[] = [];
let timer: number | null = null;

export function track(
  name: string,
  detail: { subject_type?: string; subject_id?: string; context?: Record<string, unknown> } = {}
) {
  queue.push({ name, occurred_at: new Date().toISOString(), ...detail });
  if (queue.length >= MAX_BATCH) {
    void flush();
    return;
  }
  if (timer === null) {
    timer = window.setTimeout(() => void flush(), FLUSH_INTERVAL_MS);
  }
}

export async function flush() {
  if (timer !== null) {
    window.clearTimeout(timer);
    timer = null;
  }
  if (queue.length === 0 || !window.localStorage.getItem("auth_token")) return;
  const batch = queue.slice(0, MAX_BATCH);
  queue = queue.slice(batch.length);
  try {
    await fetch(`${API_BASE}/events`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ events: batch }),
      keepalive: true,
    });
  } catch {
    queue = [...batch, ...queue].slice(0, MAX_BATCH * 4);
  }
}

export function startAnalytics() {
  window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") void flush();
  });
  window.addEventListener("pagehide", () => void flush());
}
