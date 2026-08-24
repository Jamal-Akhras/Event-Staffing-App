import { useCallback, useEffect, useState } from "react";

import { fetchPublicJson } from "./api";

export type Market = {
  market_id: string;
  name: string;
  country: string;
  currency: string;
  timezone: string;
  high_pay_threshold: string;
};

export function useMarkets() {
  const [markets, setMarkets] = useState<Market[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const retry = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchPublicJson<Market[]>("/markets")
      .then((data) => setMarkets(data))
      .catch((err: Error) => {
        setMarkets(null);
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    retry();
  }, [retry]);

  return { markets, loading, error, retry };
}
