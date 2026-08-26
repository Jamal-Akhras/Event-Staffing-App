export const CLERK_PUBLISHABLE_KEY = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "";
export const SSO_ENABLED = CLERK_PUBLISHABLE_KEY.length > 0;
export const APP_SCHEME = "venueos";

export type SsoStrategy = "oauth_google" | "oauth_apple";

export const SSO_PROVIDERS: { strategy: SsoStrategy; label: string }[] = [
  { strategy: "oauth_google", label: "Continue with Google" },
  { strategy: "oauth_apple", label: "Continue with Apple" },
];
