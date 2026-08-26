import { useState, FormEvent } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { LegalLinks } from "../components/LegalLinks";
import { SsoButtons } from "../components/SsoButtons";
import { useAuth } from "../contexts/AuthContext";
import { SSO_ENABLED } from "../lib/clerk";
import "./LoginPage.css";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(
    params.get("sso") === "incomplete" ? "That sign-in didn't complete. Try again or use your email and password." : null
  );
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
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
            Staffing your venue<br />
            starts with <em>the right people.</em>
          </h2>
          <ul className="auth-features">
            <li className="auth-feature">
              <span className="auth-feature-icon" aria-hidden="true" />
              Post shifts and receive applications in minutes
            </li>
            <li className="auth-feature">
              <span className="auth-feature-icon" aria-hidden="true" />
              Reliability scores keep your team consistent
            </li>
            <li className="auth-feature">
              <span className="auth-feature-icon" aria-hidden="true" />
              Built for UK and UAE venues with local compliance
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
          <h1 className="auth-heading">Welcome back</h1>
          <p className="auth-subheading">
            Sign in to manage your venue. Workers — use the mobile app.
          </p>
          {SSO_ENABLED && (
            <>
              <SsoButtons />
              <div className="auth-divider">or with email</div>
            </>
          )}
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
                autoComplete="current-password"
                placeholder="••••••••"
              />
            </label>
            {error && <p className="auth-error">{error}</p>}
            <button type="submit" className="auth-btn" disabled={loading}>
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <p className="auth-link-row">
            No account?{" "}
            <Link to="/register" className="auth-link">
              Register your venue
            </Link>
          </p>
          <p className="auth-link-row">
            <Link to="/forgot-password" className="auth-link">
              Forgot password?
            </Link>
          </p>
          <LegalLinks className="auth-legal-links" />
        </div>
      </main>
    </div>
  );
}
