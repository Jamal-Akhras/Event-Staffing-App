import React from "react";
import ReactDOM from "react-dom/client";
import { ClerkProvider } from "@clerk/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";
import { AppErrorFallback } from "./components/AppErrorFallback";
import { CLERK_PUBLISHABLE_KEY, SSO_ENABLED } from "./lib/clerk";
import { startAnalytics } from "./lib/analytics";
import { SentryErrorBoundary } from "./lib/observability";
import "./styles.css";

startAnalytics();

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

const app = (
  <SentryErrorBoundary
    fallback={({ resetError }) => <AppErrorFallback resetError={resetError} />}
  >
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </SentryErrorBoundary>
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {SSO_ENABLED ? <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>{app}</ClerkProvider> : app}
  </React.StrictMode>
);
