import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { AppState } from "react-native";

import { fetchWorker } from "../lib/api";
import { RatingModal } from "../screens/shifts/RatingModal";
import type { PendingRating } from "../types";
import { useAuth } from "./AuthContext";

type RatingPromptContextValue = {
  refreshRatingPrompt: () => Promise<void>;
};

const RatingPromptContext = createContext<RatingPromptContextValue | null>(null);

export function RatingPromptProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [prompt, setPrompt] = useState<PendingRating | null>(null);
  const dismissed = useRef(new Set<string>());
  const inFlight = useRef(false);

  const refreshRatingPrompt = useCallback(async () => {
    if (!user || inFlight.current) return;
    inFlight.current = true;
    try {
      const pending = await fetchWorker<PendingRating[]>("/ratings/pending?limit=1");
      const next = pending.find((item) => !dismissed.current.has(item.booking_id)) ?? null;
      setPrompt(next);
    } catch {
      setPrompt(null);
    } finally {
      inFlight.current = false;
    }
  }, [user]);

  useEffect(() => {
    dismissed.current.clear();
    void refreshRatingPrompt();
  }, [user?.user_id, refreshRatingPrompt]);

  useEffect(() => {
    const listener = AppState.addEventListener("change", (state) => {
      if (state === "active") void refreshRatingPrompt();
    });
    return () => listener.remove();
  }, [refreshRatingPrompt]);

  return (
    <RatingPromptContext.Provider value={{ refreshRatingPrompt }}>
      {children}
      {prompt && (
        <RatingModal
          rating={prompt}
          onDone={() => setPrompt(null)}
          onSkip={() => {
            dismissed.current.add(prompt.booking_id);
            setPrompt(null);
          }}
        />
      )}
    </RatingPromptContext.Provider>
  );
}

export function useRatingPrompt() {
  const context = useContext(RatingPromptContext);
  if (!context) throw new Error("useRatingPrompt must be used within RatingPromptProvider");
  return context;
}
