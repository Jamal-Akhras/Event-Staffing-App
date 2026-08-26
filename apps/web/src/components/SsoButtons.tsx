import { useState } from "react";
import { useSignIn } from "@clerk/react";

import { SSO_PROVIDERS, type SsoStrategy } from "../lib/clerk";

export function SsoButtons() {
  const { signIn } = useSignIn();
  const [pending, setPending] = useState<SsoStrategy | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function start(strategy: SsoStrategy) {
    setError(null);
    setPending(strategy);
    const { error: ssoError } = await signIn.sso({
      strategy,
      redirectUrl: "/sso-complete",
      redirectCallbackUrl: "/sso-callback",
    });
    if (ssoError) {
      setError((ssoError as { message?: string }).message ?? "We couldn't start the sign-in. Try again.");
      setPending(null);
    }
  }

  return (
    <div className="auth-sso">
      {SSO_PROVIDERS.map((provider) => (
        <button
          key={provider.strategy}
          type="button"
          className="auth-sso-btn"
          disabled={pending !== null}
          onClick={() => start(provider.strategy)}
        >
          <ProviderIcon strategy={provider.strategy} />
          <span>{pending === provider.strategy ? "Opening…" : provider.label}</span>
        </button>
      ))}
      {error && <p className="auth-error">{error}</p>}
    </div>
  );
}

function ProviderIcon({ strategy }: { strategy: SsoStrategy }) {
  if (strategy === "oauth_google") {
    return (
      <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
        <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.8 2.4 30.3 0 24 0 14.6 0 6.5 5.4 2.6 13.3l7.9 6.1C12.4 13.7 17.7 9.5 24 9.5z" />
        <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h12.7c-.6 3-2.2 5.5-4.7 7.2l7.6 5.9c4.4-4.1 6.9-10.1 6.9-17.1z" />
        <path fill="#FBBC05" d="M10.5 28.6c-.5-1.5-.8-3-.8-4.6s.3-3.1.8-4.6l-7.9-6.1C1 16.6 0 20.2 0 24s1 7.4 2.6 10.7l7.9-6.1z" />
        <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.6-5.9c-2.1 1.4-4.9 2.3-8.3 2.3-6.3 0-11.6-4.2-13.5-9.9l-7.9 6.1C6.5 42.6 14.6 48 24 48z" />
      </svg>
    );
  }
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M16.4 12.7c0-2.5 2-3.7 2.1-3.8-1.2-1.7-3-1.9-3.6-2-1.5-.2-3 .9-3.8.9-.8 0-2-.9-3.3-.8-1.7 0-3.2 1-4.1 2.5-1.8 3-.5 7.6 1.3 10.1.9 1.2 1.9 2.6 3.2 2.6 1.3-.1 1.8-.8 3.3-.8s2 .8 3.3.8c1.4 0 2.3-1.3 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9-.1 0-2.9-1.1-2.9-4.1zM14 5.3c.7-.9 1.2-2 1-3.2-1 0-2.3.7-3 1.6-.7.8-1.2 2-1.1 3.1 1.2.1 2.3-.6 3.1-1.5z" />
    </svg>
  );
}
