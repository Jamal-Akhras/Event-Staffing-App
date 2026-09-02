import { useEffect, useState } from "react";

import { fetchPublicJson } from "../../lib/api";

export type JoinCodePreview = {
  code: string;
  venue_name: string;
  relationship_type: string;
  default_role: string | null;
};

export function useJoinCodePreview(code: string) {
  const [preview, setPreview] = useState<JoinCodePreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  const trimmed = code.trim().toUpperCase();

  useEffect(() => {
    if (trimmed.length < 4) {
      setPreview(null);
      setError(null);
      return;
    }
    let cancelled = false;
    setChecking(true);
    const timer = setTimeout(async () => {
      try {
        const found = await fetchPublicJson<JoinCodePreview>(`/join-codes/${trimmed}`);
        if (!cancelled) {
          setPreview(found);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setPreview(null);
          setError((err as Error).message);
        }
      } finally {
        if (!cancelled) setChecking(false);
      }
    }, 400);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [trimmed]);

  return { preview, error, checking };
}
