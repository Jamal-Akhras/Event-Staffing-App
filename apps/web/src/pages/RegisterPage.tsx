import { Link, useSearchParams } from "react-router-dom";
import { useAuth as useClerkAuth } from "@clerk/react";

import { SsoButtons } from "../components/SsoButtons";
import { SSO_ENABLED } from "../lib/clerk";
import { RegisterForm } from "./register/RegisterForm";
import "./LoginPage.css";

export function RegisterPage() {
  const [params] = useSearchParams();
  const ssoEmail = params.get("email");
  const ssoMode = SSO_ENABLED && params.get("sso") === "1" && Boolean(ssoEmail);

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

          {SSO_ENABLED && !ssoMode && (
            <>
              <SsoButtons />
              <div className="auth-divider">or with email</div>
            </>
          )}

          {ssoMode ? <SsoRegisterForm email={ssoEmail!} /> : <RegisterForm />}

          <p className="auth-link-row">
            Already have an account?{" "}
            <Link to="/login" className="auth-link">
              Sign in
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}

function SsoRegisterForm({ email }: { email: string }) {
  const { getToken } = useClerkAuth();
  return <RegisterForm ssoEmail={email} getSsoToken={() => getToken()} />;
}
