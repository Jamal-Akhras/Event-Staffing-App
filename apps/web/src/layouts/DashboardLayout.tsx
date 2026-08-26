import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { NotificationBell } from "../components/NotificationBell";
import { PostShiftRatingPrompt } from "../components/PostShiftRatingPrompt";
import { useAuth } from "../contexts/AuthContext";
import { initials, useVenue } from "../lib/useVenue";
import "./DashboardLayout.css";

const NAV = [
  { path: "/app", label: "Overview", end: true },
  { path: "/app/shifts", label: "Shifts" },
  { path: "/app/applications", label: "Applications" },
  { path: "/app/templates", label: "Templates" },
  { path: "/app/workers", label: "Workers" },
  { path: "/app/analytics", label: "Analytics" },
  { path: "/app/settings", label: "Settings" },
];

export function DashboardLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const venue = useVenue();
  const [menuOpen, setMenuOpen] = useState(false);
  const venueName = venue.data?.name ?? "Your venue";

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/app" className="brand">
            <span className="brand-mark">V</span>
            <span>Venue OS</span>
          </Link>

          <nav className={`topnav ${menuOpen ? "open" : ""}`} aria-label="Main">
            {NAV.map((item) => (
              <NavLink key={item.path} to={item.path} end={item.end} className="topnav-link">
                {item.label}
              </NavLink>
            ))}
            <button
              type="button"
              className="topnav-link topnav-signout"
              onClick={() => { logout(); navigate("/login"); }}
            >
              Sign out
            </button>
          </nav>

          <div className="topbar-actions">
            <NotificationBell />
            <Link to="/app/settings" className="venue-chip" title={venueName}>
              <span className="venue-chip-mark">{initials(venueName)}</span>
              <span className="venue-chip-name">{venueName}</span>
            </Link>
            <button
              type="button"
              className="menu-toggle"
              aria-label={menuOpen ? "Close navigation" : "Open navigation"}
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <span />
              <span />
            </button>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="content-wrapper"><Outlet /></div>
      </main>
      <PostShiftRatingPrompt />
    </div>
  );
}
