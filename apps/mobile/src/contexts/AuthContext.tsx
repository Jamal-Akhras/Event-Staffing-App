import AsyncStorage from "@react-native-async-storage/async-storage";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { postPublicJson, setApiAuth, setUnauthorizedHandler } from "../lib/api";

export type AuthUser = {
  user_id: string;
  worker_profile_id: string | null;
  email: string;
  role: "worker" | "operator";
  currency: string;
};

type AuthContextType = {
  user: AuthUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
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
};

async function callAuthEndpoint(path: string, body: object): Promise<AuthUser> {
  const data = await postPublicJson<TokenResponse>(path, body);
  const user: AuthUser = {
    user_id: data.user_id,
    worker_profile_id: data.worker_profile_id ?? null,
    email: data.email,
    role: data.role as "worker" | "operator",
    currency: data.currency ?? "GBP",
  };
  await AsyncStorage.multiSet([
    [TOKEN_KEY, data.access_token],
    [USER_KEY, JSON.stringify(user)],
  ]);
  setApiAuth(data.access_token, user.worker_profile_id ?? user.user_id);
  return user;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(async (): Promise<void> => {
    await AsyncStorage.multiRemove([TOKEN_KEY, USER_KEY]);
    setApiAuth(null, null);
    setUser(null);
  }, []);

  useEffect(() => {
    async function restore() {
      try {
        const [[, token], [, rawUser]] = await AsyncStorage.multiGet([TOKEN_KEY, USER_KEY]);
        if (token && rawUser) {
          const stored = JSON.parse(rawUser) as AuthUser;
          setApiAuth(token, stored.worker_profile_id ?? stored.user_id);
          setUser(stored);
        }
      } catch {
        // ignore restore errors — user will need to log in
      } finally {
        setIsLoading(false);
      }
    }
    restore();
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  async function login(email: string, password: string): Promise<void> {
    const authUser = await callAuthEndpoint("/auth/login", { email, password });
    setUser(authUser);
  }

  async function register(email: string, password: string): Promise<void> {
    const authUser = await callAuthEndpoint("/auth/register", { email, password });
    setUser(authUser);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
