import { HandleSSOCallback } from "@clerk/react";
import { useNavigate } from "react-router-dom";

export function SsoCallbackPage() {
  const navigate = useNavigate();
  return (
    <div className="auth-page auth-page-centered">
      <p className="auth-subheading">Finishing sign-in…</p>
      <HandleSSOCallback
        navigateToApp={() => navigate("/sso-complete", { replace: true })}
        navigateToSignIn={() => navigate("/login?sso=incomplete", { replace: true })}
        navigateToSignUp={() => navigate("/login?sso=incomplete", { replace: true })}
      />
    </div>
  );
}
