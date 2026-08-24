import { useCallback, useEffect, useRef, useState } from "react";

import { fetchJson } from "../lib/api";
import { RatingModal, type PendingRating } from "../pages/workers/RatingModal";

export function PostShiftRatingPrompt() {
  const [prompt, setPrompt] = useState<PendingRating | null>(null);
  const dismissed = useRef(new Set<string>());
  const inFlight = useRef(false);

  const refresh = useCallback(async () => {
    if (inFlight.current) return;
    inFlight.current = true;
    try {
      const pending = await fetchJson<PendingRating[]>("/ratings/pending?limit=1");
      const next = pending.find((item) => !dismissed.current.has(item.booking_id)) ?? null;
      setPrompt(next);
    } catch {
      setPrompt(null);
    } finally {
      inFlight.current = false;
    }
  }, []);

  useEffect(() => {
    void refresh();
    window.addEventListener("focus", refresh);
    const interval = window.setInterval(refresh, 30_000);
    return () => {
      window.removeEventListener("focus", refresh);
      window.clearInterval(interval);
    };
  }, [refresh]);

  if (!prompt) return null;
  return (
    <RatingModal
      rating={prompt}
      onDone={() => setPrompt(null)}
      onClose={() => {
        dismissed.current.add(prompt.booking_id);
        setPrompt(null);
      }}
    />
  );
}
