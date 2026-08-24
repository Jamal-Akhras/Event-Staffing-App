import { useEffect, useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { Icon } from "../components/Icon";
import { NotificationBell } from "../components/NotificationBell";
import { PostShiftRatingPrompt } from "../components/PostShiftRatingPrompt";
import { API_BASE } from "../lib/api";
import "./DashboardLayout.css";

type HealthStatus = {
  status: string;
};

const NAV_SECTIONS = [
  {
    label: "Main",
    items: [
      { path: "/app", label: "Overview", icon: "overview" },
      { path: "/app/shifts", label: "Shifts", icon: "shifts" },
      { path: "/app/applications", label: "Applications", icon: "applications" },
      { path: "/app/schedule", label: "Schedule", icon: "schedule" },
    ],
  },
  {
    label: "Manage",
    items: [
      { path: "/app/templates", label: "Templates", icon: "templates" },
      { path: "/app/workers", label: "Workers", icon: "workers" },
      { path: "/app/analytics", label: "Analytics", icon: "analytics" },
      { path: "/app/settings", label: "Settings", icon: "settings" },
    ],
  },
] as const;

export function DashboardLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE}/health`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => setHealth(data))
      .catch((err) => {
        if ((err as Error).name !== "AbortError") {
          setError((err as Error).message);
        }
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    setIsSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="dashboard-layout">
      <button
        className="mobile-nav-toggle"
        type="button"
        aria-label="Open navigation"
        onClick={() => setIsSidebarOpen(true)}
      >
        <span />
        <span />
        <span />
      </button>

      {isSidebarOpen && (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Close navigation"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${isSidebarOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <div className="brand">
            <span className="brand-mark">V</span>
            <div>
              <p className="brand-title">Venue OS</p>
              <p className="brand-eyebrow">Reliability-first staffing</p>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label} className="nav-section">
              <p className="nav-section-label">{section.label}</p>
              {section.items.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`nav-item ${isActive ? "active" : ""}`}
                    onClick={() => setIsSidebarOpen(false)}
                  >
                    <span className="nav-active-marker" aria-hidden="true" />
                    <Icon name={item.icon} size={18} className="nav-icon" />
                    <span className="nav-label">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          {user && (
            <div className="sidebar-user">
              <div className="sidebar-user-email">{user.email}</div>
              <button
                type="button"
                className="sidebar-logout-btn"
                onClick={() => { logout(); navigate("/login"); }}
              >
                Sign out
              </button>
            </div>
          )}
          <div className="api-status">
            <span className="status-label">API Status</span>
            {error && <span className="status error">Error</span>}
            {!error && !health && <span className="status pending">Checking</span>}
            {health && <span className="status ok">Healthy</span>}
          </div>
        </div>
      </aside>

      <div className="dashboard-utilities">
        <NotificationBell />
      </div>

      <main className="main-content">
        <div className="content-wrapper"><Outlet /></div>
      </main>
      <PostShiftRatingPrompt />
    </div>
  );
}
