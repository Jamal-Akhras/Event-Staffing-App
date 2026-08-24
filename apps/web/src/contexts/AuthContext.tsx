import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { postPublicJson, setUnauthorizedHandler } from "../lib/api";

type AuthUser = {
  user_id: string;
  email: string;
  role: string;
  account_id: string | null;
  organisation_id: string | null;
  venue_id: string | null;
  currency: string;
};

type AuthContextType = {
  user: AuthUser | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

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

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(loadToken);
  const [user, setUser] = useState<AuthUser | null>(loadUser);

  async function login(email: string, password: string): Promise<void> {
    const data = await postPublicJson<{
      access_token: string;
      user_id: string;
      email: string;
      role: string;
      account_id?: string | null;
      organisation_id?: string | null;
      venue_id?: string | null;
      currency?: string;
    }>("/auth/login", { email, password });
    const authUser: AuthUser = {
      user_id: data.user_id,
      email: data.email,
      role: data.role,
      account_id: data.account_id ?? null,
      organisation_id: data.organisation_id ?? null,
      venue_id: data.venue_id ?? data.account_id ?? null,
      currency: data.currency ?? "GBP",
    };
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(authUser));
    setToken(data.access_token);
    setUser(authUser);
  }

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout();
      navigate("/login", { replace: true });
    });
    return () => setUnauthorizedHandler(null);
  }, [logout, navigate]);

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
