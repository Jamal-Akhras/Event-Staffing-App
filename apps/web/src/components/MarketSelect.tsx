import type { Market } from "../lib/useMarkets";

type MarketSelectProps = {
  markets: Market[] | null;
  loading: boolean;
  error: string | null;
  value: string;
  onChange: (marketId: string) => void;
  onRetry: () => void;
  country?: string;
};

export function MarketSelect({
  markets,
  loading,
  error,
  value,
  onChange,
  onRetry,
  country,
}: MarketSelectProps) {
  if (loading) {
    return (
      <select className="form-input" disabled value="">
        <option value="">Loading cities…</option>
      </select>
    );
  }

  if (error || markets === null) {
    return (
      <div className="market-select-error">
        <p className="auth-error" style={{ margin: 0 }}>
          {error ?? "Couldn't load available cities."}
        </p>
        <button type="button" className="auth-link" style={{ background: "none", border: 0, padding: 0, cursor: "pointer" }} onClick={onRetry}>
          Try again
        </button>
      </div>
    );
  }

  const options = country ? markets.filter((market) => market.country === country) : markets;

  if (options.length === 0) {
    return (
      <p className="auth-error" style={{ margin: 0 }}>
        No launch cities are available {country ? "in this country" : ""} yet.
      </p>
    );
  }

  return (
    <select
      className="form-input"
      value={value}
      required
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="" disabled>
        Select your city…
      </option>
      {options.map((market) => (
        <option key={market.market_id} value={market.market_id}>
          {market.name}
        </option>
      ))}
    </select>
  );
}
