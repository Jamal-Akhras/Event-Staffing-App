import { BrowserRouter, Navigate, Routes, Route } from "react-router-dom";
import { ToastProvider } from "./components/Toast";
import { AuthProvider } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { DashboardLayout } from "./layouts/DashboardLayout";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { JoinTeamPage } from "./pages/JoinTeamPage";
import { SsoCallbackPage } from "./pages/SsoCallbackPage";
import { SsoCompletePage } from "./pages/SsoCompletePage";
import { SSO_ENABLED } from "./lib/clerk";
import { DashboardPage } from "./pages/DashboardPage";
import { ShiftsPage } from "./pages/ShiftsPage";
import { TemplatesPage } from "./pages/TemplatesPage";
import { ApplicationsPage } from "./pages/ApplicationsPage";
import { WorkersPage } from "./pages/WorkersPage";
import { TimesheetPage } from "./pages/TimesheetPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { CookiesPage, PrivacyPage, TermsPage } from "./pages/LegalPage";
import { PublicLayout } from "./pages/public/PublicLayout";
import { HomePage } from "./pages/public/HomePage";
import {
  DownloadPage,
  EmployerLandingPage,
  SafetyPage,
  WorkerLandingPage,
} from "./pages/public/AudiencePages";

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            <Route element={<PublicLayout />}>
              <Route index element={<HomePage />} />
              <Route path="/for-workers" element={<WorkerLandingPage />} />
              <Route path="/for-employers" element={<EmployerLandingPage />} />
              <Route path="/download" element={<DownloadPage />} />
              <Route path="/safety" element={<SafetyPage />} />
            </Route>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/join-team" element={<JoinTeamPage />} />
            {SSO_ENABLED && <Route path="/sso-callback" element={<SsoCallbackPage />} />}
            {SSO_ENABLED && <Route path="/sso-complete" element={<SsoCompletePage />} />}
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ForgotPasswordPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/cookies" element={<CookiesPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/app" element={<DashboardLayout />}>
                <Route index element={<DashboardPage />} />
                <Route path="shifts" element={<ShiftsPage />} />
                <Route path="templates" element={<TemplatesPage />} />
                <Route path="applications" element={<ApplicationsPage />} />
                <Route path="workers" element={<WorkersPage />} />
                <Route path="timesheet" element={<TimesheetPage />} />
                <Route path="schedule" element={<Navigate to="/app/shifts" replace />} />
                <Route path="analytics" element={<AnalyticsPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
            </Route>
            {[
              "shifts",
              "templates",
              "applications",
              "workers",
              "timesheet",
              "schedule",
              "analytics",
              "settings",
            ].map((route) => (
              <Route key={route} path={`/${route}`} element={<Navigate to={`/app/${route}`} replace />} />
            ))}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
