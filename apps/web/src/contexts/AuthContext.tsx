import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, postJson, postPublicJson, setUnauthorizedHandler } from "../lib/api";

type AuthUser = {
  user_id: string;
  email: string;
  role: string;
  account_id: string | null;
  organisation_id: string | null;
  venue_id: string | null;
  currency: string;
};

export type SessionPayload = {
  access_token: string;
  user_id: string;
  email: string;
  role: string;
  account_id?: string | null;
  organisation_id?: string | null;
  venue_id?: string | null;
  currency?: string;
};

type AuthContextType = {
  user: AuthUser | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  loginWithSso: (ssoToken: string) => Promise<void>;
  acceptSession: (session: SessionPayload) => void;
  logOff: () => Promise<void>;
  logout: () => void;
};

export class SsoRegistrationRequiredError extends Error {
  email: string;

  constructor(email: string) {
    super("No venue account exists for this email yet.");
    this.name = "SsoRegistrationRequiredError";
    this.email = email;
  }
}

const AuthContext = createContext<AuthContextType | null>(null);

const TOKEN_KEY = "auth_token";
const USER_KEY = "auth_user";

function loadToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function loadUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

function toAuthUser(data: SessionPayload): AuthUser {
  return {
    user_id: data.user_id,
    email: data.email,
    role: data.role,
    account_id: data.account_id ?? null,
    organisation_id: data.organisation_id ?? null,
    venue_id: data.venue_id ?? data.account_id ?? null,
    currency: data.currency ?? "GBP",
  };
}

function registrationRequiredEmail(err: unknown): string | null {
  if (!(err instanceof ApiError) || err.status !== 404 || !err.serverDetail) return null;
  try {
    const detail = JSON.parse(err.serverDetail) as { code?: string; email?: string };
    return detail.code === "SSO_REGISTRATION_REQUIRED" && detail.email ? detail.email : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(loadToken);
  const [user, setUser] = useState<AuthUser | null>(loadUser);

  const acceptSession = useCallback((data: SessionPayload) => {
    const authUser = toAuthUser(data);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(authUser));
    setToken(data.access_token);
    setUser(authUser);
  }, []);

  async function login(email: string, password: string): Promise<void> {
    acceptSession(await postPublicJson<SessionPayload>("/auth/login", { email, password }));
  }

  async function loginWithSso(ssoToken: string): Promise<void> {
    try {
      acceptSession(await postPublicJson<SessionPayload>("/auth/sso", { token: ssoToken, role: "operator" }));
    } catch (err) {
      const email = registrationRequiredEmail(err);
      if (email) throw new SsoRegistrationRequiredError(email);
      throw err;
    }
  }

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const logOff = useCallback(async () => {
    await postJson("/auth/logout");
    logout();
  }, [logout]);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout();
      navigate("/login", { replace: true });
    });
    return () => setUnauthorizedHandler(null);
  }, [logout, navigate]);

  return (
    <AuthContext.Provider value={{ user, token, login, loginWithSso, acceptSession, logOff, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
