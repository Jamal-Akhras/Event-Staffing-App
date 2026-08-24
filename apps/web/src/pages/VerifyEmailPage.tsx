import { useEffect, useRef, useState, FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { LegalLinks } from "../components/LegalLinks";
import { ApiError, postPublicJson } from "../lib/api";
import "./LoginPage.css";

type Status = "missing" | "verifying" | "success" | "error" | "resent";

function errorText(err: unknown): string {
  if (err instanceof ApiError && err.serverDetail) return err.serverDetail;
  return (err as Error).message;
}

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [status, setStatus] = useState<Status>(token ? "verifying" : "missing");
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const started = useRef(false);

  useEffect(() => {
    if (!token || started.current) return;
    started.current = true;
    postPublicJson("/auth/verify-email", { token })
      .then(() => setStatus("success"))
      .catch((err) => {
        setError(errorText(err));
        setStatus("error");
      });
  }, [token]);

  async function handleResend(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await postPublicJson("/auth/resend-verification", { email });
      setStatus("resent");
    } catch (err) {
      setError(errorText(err));
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
          <h2 className="auth-left-headline">Confirm your<br />email</h2>
        </div>
        <div className="auth-left-footer">
          <p className="auth-trust">UK GDPR &amp; UAE PDPL compliant · Bcrypt + JWT</p>
          <p className="auth-copyright">© 2026 Venue OS. All rights reserved.</p>
        </div>
      </aside>

      <main className="auth-panel-right">
        <div className="auth-form-wrap">
          {status === "verifying" && (
            <>
              <h1 className="auth-heading">Verifying…</h1>
              <p className="auth-subheading">Confirming your email address.</p>
            </>
          )}

          {status === "success" && (
            <>
              <h1 className="auth-heading">Email verified!</h1>
              <p className="auth-subheading">Your account is confirmed. You can now sign in.</p>
              <Link to="/login" className="auth-btn" style={{ textAlign: "center", display: "block" }}>
                Go to Sign In
              </Link>
            </>
          )}

          {status === "resent" && (
            <>
              <h1 className="auth-heading">Check your inbox</h1>
              <p className="auth-subheading">
                If that email needs verification, a new link has been sent.
              </p>
              <Link to="/login" className="auth-link">← Back to Sign In</Link>
            </>
          )}

          {(status === "error" || status === "missing") && (
            <>
              <h1 className="auth-heading">
                {status === "missing" ? "Verification link incomplete" : "Verification failed"}
              </h1>
              <p className="auth-subheading">
                {status === "missing"
                  ? "This page needs the verification link from your email. Open the link directly, or request a new one below."
                  : "This link is invalid or has already been used. Request a new one below."}
              </p>
              {status === "error" && error && <p className="auth-error">{error}</p>}
              <form onSubmit={handleResend} className="auth-form">
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
                <button type="submit" className="auth-btn" disabled={loading}>
                  {loading ? "Sending…" : "Resend Verification Email"}
                </button>
              </form>
              <p className="auth-link-row">
                <Link to="/login" className="auth-link">← Back to Sign In</Link>
              </p>
            </>
          )}
          <LegalLinks className="auth-legal-links" />
        </div>
      </main>
    </div>
  );
}
