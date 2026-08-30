import { AppState } from "react-native";

import { API_BASE, getClientHeaders, isAuthenticated } from "./api";

const FLUSH_INTERVAL_MS = 5000;
const MAX_BATCH = 25;
const EVENT_VERSION = 1;

export type EventDetail = {
  subject_type?: string;
  subject_id?: string;
  context?: Record<string, unknown>;
  slate_id?: string;
  position?: number;
  dwell_ms?: number;
};

type TrackedEvent = EventDetail & {
  name: string;
  occurred_at: string;
  event_version: number;
};

let queue: TrackedEvent[] = [];
let timer: ReturnType<typeof setTimeout> | null = null;
const counted = new Set<string>();

export function track(name: string, detail: EventDetail = {}, occurredAt?: number) {
  queue.push({
    name,
    occurred_at: new Date(occurredAt ?? Date.now()).toISOString(),
    event_version: EVENT_VERSION,
    ...detail,
  });
  if (queue.length >= MAX_BATCH) {
    void flush();
    return;
  }
  if (timer === null) {
    timer = setTimeout(() => void flush(), FLUSH_INTERVAL_MS);
  }
}

export function trackOnce(key: string, name: string, detail: EventDetail = {}, occurredAt?: number) {
  if (counted.has(key)) return;
  counted.add(key);
  track(name, detail, occurredAt);
}

export function resetSeen() {
  counted.clear();
}

export async function flush() {
  if (timer !== null) {
    clearTimeout(timer);
    timer = null;
  }
  if (queue.length === 0 || !isAuthenticated()) return;
  const batch = queue.slice(0, MAX_BATCH);
  queue = queue.slice(batch.length);
  try {
    await fetch(`${API_BASE}/events`, {
      method: "POST",
      headers: getClientHeaders(),
      body: JSON.stringify({ events: batch }),
    });
  } catch {
    queue = [...batch, ...queue].slice(0, MAX_BATCH * 4);
  }
}

export function startAnalytics() {
  return AppState.addEventListener("change", (state) => {
    if (state !== "active") void flush();
  });
}
