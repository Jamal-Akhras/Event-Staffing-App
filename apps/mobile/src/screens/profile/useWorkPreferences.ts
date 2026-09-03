import { useEffect, useState } from "react";

import { fetchWorker, putWorker } from "../../lib/api";
import type { WorkerContext } from "../../types";

export function useWorkPreferences() {
  const [marketplaceEnabled, setMarketplaceEnabled] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchWorker<WorkerContext>("/me/work-context")
      .then((context) => {
        if (active) setMarketplaceEnabled(context.marketplace_enabled);
      })
      .catch((err) => {
        if (active) setError((err as Error).message);
      });
    return () => {
      active = false;
    };
  }, []);

  const setMarketplace = async (value: boolean) => {
    const previous = marketplaceEnabled;
    setMarketplaceEnabled(value);
    setError(null);
    try {
      await putWorker("/me/work-preferences", { marketplace_enabled: value });
    } catch (err) {
      setMarketplaceEnabled(previous);
      setError((err as Error).message);
    }
  };

  return { marketplaceEnabled, setMarketplace, error };
}
