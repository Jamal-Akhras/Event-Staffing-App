import * as Sentry from "@sentry/react";

const dsn = (import.meta.env.VITE_SENTRY_DSN as string | undefined) ?? "";
const environment = (import.meta.env.MODE as string | undefined) ?? "development";

if (dsn) {
  Sentry.init({
    dsn,
    environment,
    tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE ?? 0),
    sendDefaultPii: false,
  });
}

export const SentryErrorBoundary = Sentry.ErrorBoundary;
