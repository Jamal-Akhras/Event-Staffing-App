import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";

import { postPublicJson, setApiAuth, setUnauthorizedHandler } from "../lib/api";
import { deleteItem, getItem, setItem } from "../lib/secureStorage";
import { unregisterStoredPushDevice } from "../lib/pushRegistration";

export type AuthUser = {
  user_id: string;
  worker_profile_id: string | null;
  email: string;
  role: "worker" | "operator";
  currency: string;
  organisation_id: string | null;
  venue_id: string | null;
};

type AuthContextType = {
  user: AuthUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithSso: (ssoToken: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

const TOKEN_KEY = "auth_token";
const USER_KEY = "auth_user";

type TokenResponse = {
  access_token: string;
  user_id: string;
  worker_profile_id?: string | null;
  email: string;
  role: string;
  currency?: string;
  organisation_id?: string | null;
  venue_id?: string | null;
};

async function saveSession(token: string, user: AuthUser): Promise<void> {
  await Promise.all([
    setItem(TOKEN_KEY, token),
    setItem(USER_KEY, JSON.stringify(user)),
  ]);
}

async function clearSession(): Promise<void> {
  await Promise.all([
    deleteItem(TOKEN_KEY),
    deleteItem(USER_KEY),
  ]);
}

async function readSession(): Promise<{ token: string; rawUser: string } | null> {
  const [token, rawUser] = await Promise.all([
    getItem(TOKEN_KEY),
    getItem(USER_KEY),
  ]);
  return token && rawUser ? { token, rawUser } : null;
}

async function callAuthEndpoint(path: string, body: object): Promise<AuthUser> {
  const data = await postPublicJson<TokenResponse>(path, body);
  const user: AuthUser = {
    user_id: data.user_id,
    worker_profile_id: data.worker_profile_id ?? null,
    email: data.email,
    role: data.role as "worker" | "operator",
    currency: data.currency ?? "GBP",
    organisation_id: data.organisation_id ?? null,
    venue_id: data.venue_id ?? null,
  };
  await saveSession(data.access_token, user);
  setApiAuth(data.access_token, user.worker_profile_id ?? user.user_id);
  return user;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const logoutInFlight = useRef(false);

  const performLogout = useCallback(async (unregisterDevice: boolean): Promise<void> => {
    if (logoutInFlight.current) return;
    logoutInFlight.current = true;
    try {
      if (unregisterDevice) await unregisterStoredPushDevice().catch(() => undefined);
      await clearSession();
      setApiAuth(null, null);
      setUser(null);
    } finally {
      logoutInFlight.current = false;
    }
  }, []);

  const logout = useCallback(() => performLogout(true), [performLogout]);

  useEffect(() => {
    async function restore() {
      try {
        const session = await readSession();
        if (session) {
          const stored = JSON.parse(session.rawUser) as AuthUser;
          setApiAuth(session.token, stored.worker_profile_id ?? stored.user_id);
          setUser(stored);
        }
      } catch {
        await clearSession();
      } finally {
        setIsLoading(false);
      }
    }
    restore();
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => performLogout(false));
    return () => setUnauthorizedHandler(null);
  }, [performLogout]);

  async function login(email: string, password: string): Promise<void> {
    const authUser = await callAuthEndpoint("/auth/login", { email, password });
    setUser(authUser);
  }

  async function loginWithSso(ssoToken: string): Promise<void> {
    const authUser = await callAuthEndpoint("/auth/sso", { token: ssoToken, role: "worker" });
    setUser(authUser);
  }

  async function register(email: string, password: string): Promise<void> {
    const authUser = await callAuthEndpoint("/auth/register", { email, password });
    setUser(authUser);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, loginWithSso, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
