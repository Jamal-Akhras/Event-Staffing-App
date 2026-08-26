export const CLERK_PUBLISHABLE_KEY: string = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "";
export const SSO_ENABLED = CLERK_PUBLISHABLE_KEY.length > 0;

export type SsoStrategy = "oauth_google" | "oauth_apple";

export const SSO_PROVIDERS: { strategy: SsoStrategy; label: string }[] = [
  { strategy: "oauth_google", label: "Continue with Google" },
  { strategy: "oauth_apple", label: "Continue with Apple" },
];
