import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth as useClerkAuth } from "@clerk/react";

import { SsoRegistrationRequiredError, useAuth } from "../contexts/AuthContext";

export function SsoCompletePage() {
  const navigate = useNavigate();
  const { isLoaded, isSignedIn, getToken } = useClerkAuth();
  const { loginWithSso } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (!isLoaded || started.current) return;
    if (!isSignedIn) {
      navigate("/login", { replace: true });
      return;
    }
    started.current = true;
    (async () => {
      const token = await getToken();
      if (!token) {
        setError("We couldn't confirm your sign-in. Please try again.");
        return;
      }
      try {
        await loginWithSso(token);
        navigate("/app", { replace: true });
      } catch (err) {
        if (err instanceof SsoRegistrationRequiredError) {
          navigate(`/register?sso=1&email=${encodeURIComponent(err.email)}`, { replace: true });
          return;
        }
        setError((err as Error).message);
      }
    })();
  }, [isLoaded, isSignedIn, getToken, loginWithSso, navigate]);

  return (
    <div className="auth-page auth-page-centered">
      {error ? (
        <div className="auth-form-wrap">
          <p className="auth-error">{error}</p>
          <p className="auth-link-row">
            <Link to="/login" className="auth-link">Back to sign in</Link>
          </p>
        </div>
      ) : (
        <p className="auth-subheading">Signing you in…</p>
      )}
    </div>
  );
}
