import { useEffect, useState, FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { LegalLinks } from "../components/LegalLinks";
import { MarketSelect } from "../components/MarketSelect";
import { useAuth } from "../contexts/AuthContext";
import { postPublicJson } from "../lib/api";
import { useMarkets } from "../lib/useMarkets";
import "./LoginPage.css";

export function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const { markets, loading: marketsLoading, error: marketsError, retry: retryMarkets } = useMarkets();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [organisationName, setOrganisationName] = useState("");
  const [venueName, setVenueName] = useState("");
  const [country, setCountry] = useState<"GB" | "AE">("GB");
  const [marketId, setMarketId] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

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
      await postPublicJson("/auth/register/operator", {
        email,
        password,
        ...(organisationName.trim() ? { organisation_name: organisationName.trim() } : {}),
        venue_name: venueName,
        country,
        market_id: marketId,
        invite_code: inviteCode,
      });
      setRegisteredEmail(email);
      await login(email, password);
      navigate("/app");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <aside className="auth-panel-left">
        <div className="auth-left-logo">
          <div className="auth-brand-mark">V</div>
          <div>
            <p className="auth-brand-name">Venue OS</p>
            <p className="auth-brand-tagline">Reliability-first staffing</p>
          </div>
        </div>

        <div className="auth-left-body">
          <h2 className="auth-left-headline">
            Your venue.<br />
            Your <em>team. Your rules.</em>
          </h2>
          <ul className="auth-features">
            <li className="auth-feature">
              <span className="auth-feature-icon" aria-hidden="true" />
              Set up your venue in under 2 minutes
            </li>
            <li className="auth-feature">
              <span className="auth-feature-icon" aria-hidden="true" />
              Isolated per-venue data — your shifts stay yours
            </li>
            <li className="auth-feature">
              <span className="auth-feature-icon" aria-hidden="true" />
              Available in United Kingdom and UAE
            </li>
          </ul>
        </div>

        <div className="auth-left-footer">
          <p className="auth-trust">UK GDPR &amp; UAE PDPL compliant · Bcrypt + JWT</p>
          <p className="auth-copyright">© 2026 Venue OS. All rights reserved.</p>
        </div>
      </aside>

      <main className="auth-panel-right">
        <div className="auth-form-wrap">
          <h1 className="auth-heading">Register your venue</h1>
          <p className="auth-subheading">
            Workers? Download the Venue OS app to get started.
          </p>

          <form onSubmit={handleSubmit} className="auth-form">
            <label className="form-label">
              Email address
              <input
                type="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="you@venue.com"
              />
            </label>
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
          </form>

          <p className="auth-link-row">
            Already have an account?{" "}
            <Link to="/login" className="auth-link">
              Sign in
            </Link>
          </p>
          <LegalLinks className="auth-legal-links" />
        </div>
      </main>
    </div>
  );
}
