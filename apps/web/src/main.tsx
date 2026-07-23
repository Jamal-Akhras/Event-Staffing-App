import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import { AppErrorFallback } from "./components/AppErrorFallback";
import { SentryErrorBoundary } from "./lib/observability";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <SentryErrorBoundary
      fallback={({ resetError }) => <AppErrorFallback resetError={resetError} />}
    >
      <App />
    </SentryErrorBoundary>
  </React.StrictMode>
);
