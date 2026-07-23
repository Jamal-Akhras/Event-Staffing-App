import { useState, FormEvent } from "react";
import { Link } from "react-router-dom";

import { LegalLinks } from "../components/LegalLinks";
import { postPublicJson } from "../lib/api";
import "./LoginPage.css";

type Step = "email" | "reset" | "done";

export function ForgotPasswordPage() {
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRequestReset(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await postPublicJson<{ reset_token?: string } | undefined>("/auth/forgot-password", { email });
      if (data?.reset_token) setToken(data.reset_token);
      setStep("reset");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleResetPassword(e: FormEvent) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await postPublicJson("/auth/reset-password", { token, new_password: newPassword });
      setStep("done");
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
          <h2 className="auth-left-headline">Reset your<br />password</h2>
        </div>
        <div className="auth-left-footer">
          <p className="auth-trust">UK GDPR &amp; UAE PDPL compliant · Bcrypt + JWT</p>
          <p className="auth-copyright">© 2026 Venue OS. All rights reserved.</p>
        </div>
      </aside>

      <main className="auth-panel-right">
        <div className="auth-form-wrap">
          {step === "done" ? (
            <>
              <h1 className="auth-heading">Password reset!</h1>
              <p className="auth-subheading">You can now sign in with your new password.</p>
              <Link to="/login" className="auth-btn" style={{ textAlign: "center", display: "block" }}>
                Back to Sign In
              </Link>
              <LegalLinks className="auth-legal-links" />
            </>
          ) : step === "email" ? (
            <>
              <h1 className="auth-heading">Forgot password?</h1>
              <p className="auth-subheading">Enter your email to receive a reset link.</p>
              <form onSubmit={handleRequestReset} className="auth-form">
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
                {error && <p className="auth-error">{error}</p>}
                <button type="submit" className="auth-btn" disabled={loading}>
                  {loading ? "Sending…" : "Send Reset Link"}
                </button>
              </form>
              <p className="auth-link-row">
                <Link to="/login" className="auth-link">← Back to Sign In</Link>
              </p>
              <LegalLinks className="auth-legal-links" />
            </>
          ) : (
            <>
              <h1 className="auth-heading">Reset password</h1>
              <p className="auth-subheading">Enter the reset token from your email and choose a new password.</p>
              <form onSubmit={handleResetPassword} className="auth-form">
                <label className="form-label">
                  Reset token
                  <textarea
                    className="form-input"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    required
                    rows={3}
                    placeholder="Paste your reset token here"
                    style={{ resize: "none", fontFamily: "monospace", fontSize: 12 }}
                  />
                </label>
                <label className="form-label">
                  New password
                  <input
                    type="password"
                    className="form-input"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    autoComplete="new-password"
                    placeholder="••••••••"
                  />
                </label>
                <label className="form-label">
                  Confirm password
                  <input
                    type="password"
                    className="form-input"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    placeholder="••••••••"
                  />
                </label>
                {error && <p className="auth-error">{error}</p>}
                <button type="submit" className="auth-btn" disabled={loading}>
                  {loading ? "Resetting…" : "Reset Password"}
                </button>
              </form>
              <LegalLinks className="auth-legal-links" />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
