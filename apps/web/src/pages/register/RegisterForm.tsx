import { useEffect, useState, FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";

import { LegalLinks } from "../../components/LegalLinks";
import { MarketSelect } from "../../components/MarketSelect";
import { useAuth, type SessionPayload } from "../../contexts/AuthContext";
import { postPublicJson } from "../../lib/api";
import { useMarkets } from "../../lib/useMarkets";

type RegisterFormProps = {
  ssoEmail?: string;
  getSsoToken?: () => Promise<string | null>;
};

export function RegisterForm({ ssoEmail, getSsoToken }: RegisterFormProps) {
  const { login, acceptSession } = useAuth();
  const navigate = useNavigate();
  const { markets, loading: marketsLoading, error: marketsError, retry: retryMarkets } = useMarkets();
  const [email, setEmail] = useState(ssoEmail ?? "");
  const [password, setPassword] = useState("");
  const [organisationName, setOrganisationName] = useState("");
  const [venueName, setVenueName] = useState("");
  const [country, setCountry] = useState<"GB" | "AE">("GB");
  const [marketId, setMarketId] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const usingSso = Boolean(ssoEmail && getSsoToken);

  useEffect(() => {
    if (!markets) return;
    const countryMarkets = markets.filter((market) => market.country === country);
    if (marketId && !countryMarkets.some((market) => market.market_id === marketId)) {
      setMarketId("");
      return;
    }
    if (!marketId && countryMarkets.length === 1) {
      setMarketId(countryMarkets[0].market_id);
    }
  }, [markets, country, marketId]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!marketId) {
      setError("Select the city your venue operates in.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const body = {
        email,
        ...(organisationName.trim() ? { organisation_name: organisationName.trim() } : {}),
        venue_name: venueName,
        country,
        market_id: marketId,
        invite_code: inviteCode,
      };
      if (usingSso) {
        const ssoToken = await getSsoToken!();
        if (!ssoToken) throw new Error("Your sign-in expired. Go back and sign in again.");
        acceptSession(await postPublicJson<SessionPayload>("/auth/register/operator", { ...body, sso_token: ssoToken }));
      } else {
        await postPublicJson("/auth/register/operator", { ...body, password });
        await login(email, password);
      }
      navigate("/app");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      {usingSso && (
        <p className="auth-sso-note">
          Signing up as <strong>{ssoEmail}</strong>. Tell us about your venue to finish.
        </p>
      )}
      <label className="form-label">
        Email address
        <input
          type="email"
          className="form-input"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          readOnly={usingSso}
          autoComplete="email"
          placeholder="you@venue.com"
        />
      </label>
      {!usingSso && (
        <label className="form-label">
          Password
          <input
            type="password"
            className="form-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="new-password"
            placeholder="••••••••"
          />
        </label>
      )}
      <label className="form-label">
        Organisation name <span className="auth-optional">(optional)</span>
        <input
          type="text"
          className="form-input"
          value={organisationName}
          onChange={(e) => setOrganisationName(e.target.value)}
          placeholder="e.g. Grand Hospitality Group"
        />
      </label>
      <label className="form-label">
        Venue name
        <input
          type="text"
          className="form-input"
          value={venueName}
          onChange={(e) => setVenueName(e.target.value)}
          required
          placeholder="e.g. The Grand Ballroom"
        />
      </label>
      <label className="form-label">
        Country
        <select
          className="form-input"
          value={country}
          onChange={(e) => setCountry(e.target.value as "GB" | "AE")}
        >
          <option value="GB">United Kingdom (GBP £)</option>
          <option value="AE">United Arab Emirates (AED د.إ)</option>
        </select>
      </label>
      <label className="form-label">
        City
        <MarketSelect
          markets={markets}
          loading={marketsLoading}
          error={marketsError}
          value={marketId}
          onChange={setMarketId}
          onRetry={retryMarkets}
          country={country}
        />
      </label>
      <label className="form-label">
        Invite code
        <input
          type="text"
          className="form-input"
          value={inviteCode}
          onChange={(e) => setInviteCode(e.target.value)}
          required
          placeholder="Provided by our team"
        />
      </label>
      {error && <p className="auth-error">{error}</p>}
      <p className="auth-consent">
        By creating an account you agree to our{" "}
        <Link to="/terms" className="auth-link">Terms</Link> and{" "}
        <Link to="/privacy" className="auth-link">Privacy Policy</Link>.
      </p>
      <button type="submit" className="auth-btn" disabled={loading}>
        {loading ? "Creating account…" : "Create account"}
      </button>
      <LegalLinks className="auth-legal-links" />
    </form>
  );
}
