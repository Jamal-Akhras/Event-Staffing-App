import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth, type SessionPayload } from "../contexts/AuthContext";
import { postPublicJson } from "../lib/api";
import "./LoginPage.css";

export function JoinTeamPage() {
  const { acceptSession } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const session = await postPublicJson<SessionPayload>("/auth/register/invited", {
        email,
        password,
        token: token.trim(),
      });
      acceptSession(session);
      navigate("/app");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Join your team</h1>
        <p className="login-lead">
          Use the invitation code a colleague sent you to help run their venues.
        </p>
        <form className="login-form" onSubmit={submit}>
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              required
            />
          </label>
          <label>
            Invitation code
            <input value={token} onChange={(event) => setToken(event.target.value)} required />
          </label>
          {error && <p className="login-error">{error}</p>}
          <button type="submit" disabled={busy}>
            Join
          </button>
        </form>
      </div>
    </div>
  );
}
