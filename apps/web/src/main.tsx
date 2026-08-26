import React from "react";
import ReactDOM from "react-dom/client";
import { ClerkProvider } from "@clerk/react";

import App from "./App";
import { AppErrorFallback } from "./components/AppErrorFallback";
import { CLERK_PUBLISHABLE_KEY, SSO_ENABLED } from "./lib/clerk";
import { SentryErrorBoundary } from "./lib/observability";
import "./styles.css";

const app = (
  <SentryErrorBoundary
    fallback={({ resetError }) => <AppErrorFallback resetError={resetError} />}
  >
    <App />
  </SentryErrorBoundary>
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {SSO_ENABLED ? <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>{app}</ClerkProvider> : app}
  </React.StrictMode>
);
