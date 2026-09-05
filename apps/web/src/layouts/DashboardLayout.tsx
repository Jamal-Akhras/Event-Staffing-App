import { ReactNode, useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";

import { VenueSwitcher } from "./VenueSwitcher";

import { NotificationBell } from "../components/NotificationBell";
import { PostShiftRatingPrompt } from "../components/PostShiftRatingPrompt";
import { VenueRatingBadge } from "../components/VenueRatingBadge";
import { initials, useVenue, useVenueRating } from "../lib/useVenue";
import { usePageViews } from "../lib/usePageViews";
import "./DashboardLayout.css";

type NavItem = { path: string; label: string; icon: ReactNode; end?: boolean };

const NAV: NavItem[] = [
  { path: "/app", label: "Overview", end: true, icon: icon("M3.5 3.5h7v7h-7zM13.5 3.5h7v7h-7zM3.5 13.5h7v7h-7zM13.5 13.5h7v7h-7z", true) },
  { path: "/app/shifts", label: "Schedule", icon: icon("M3.5 5h17v15.5H3.5zM3.5 9.5h17M8 3.5v3M16 3.5v3") },
  { path: "/app/applications", label: "Requests", icon: icon("M3.5 13.5 6 5.5h12l2.5 8V19a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 19zM3.5 13.5h5l1.5 2.5h4l1.5-2.5h5") },
  { path: "/app/workers", label: "People", icon: icon("M9 8a3 3 0 1 0 0 0M3.5 20c0-3 2.5-5 5.5-5s5.5 2 5.5 5M16 6.6a3 3 0 0 1 0 5.8M20.5 20c0-2.2-1.4-4-3.6-4.6") },
  { path: "/app/timesheet", label: "Timesheets", icon: icon("M12 3.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17M12 7.5V12l3 2") },
  { path: "/app/analytics", label: "Insight", icon: icon("M4 20h16M7 17v-5M12 17V8M17 17v-3") },
  { path: "/app/billing", label: "Billing", icon: icon("M6 3.5h12v17l-2-1.3-2 1.3-2-1.3-2 1.3-2-1.3zM9 8h6M9 11.5h6") },
  { path: "/app/settings", label: "Settings", icon: icon("M4 7h8M16 7h4M4 12h4M12 12h8M4 17h6M14 17h6") },
];

function icon(d: string, fill = false): ReactNode {
  return (
    <svg className="nav-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      {fill
        ? d.split("M").filter(Boolean).map((seg, i) => <path key={i} d={"M" + seg} />)
        : <path d={d} />}
    </svg>
  );
}

export function DashboardLayout() {
  const location = useLocation();
  const venue = useVenue();
  usePageViews();
  const [menuOpen, setMenuOpen] = useState(false);
  const venueName = venue.data?.name ?? "Your venue";
  const rating = useVenueRating(venue.data?.venue_id);

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  return (
    <div className={`app-shell ${menuOpen ? "menu-open" : ""}`}>
      <aside className="sidebar">
        <div className="sidebar-brand">
          <Link to="/app" className="brand">
            <span className="brand-mark">V</span>
            <span>Venue OS</span>
          </Link>
        </div>
        <nav className="sidenav" aria-label="Main">
          {NAV.map((item) => (
            <NavLink key={item.path} to={item.path} end={item.end} className="sidenav-link">
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <VenueSwitcher />
        </div>
      </aside>

      <div className="shell-main">
        <header className="appbar">
          <button
            type="button"
            className="menu-toggle"
            aria-label={menuOpen ? "Close navigation" : "Open navigation"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span />
            <span />
            <span />
          </button>
          <div className="appbar-actions">
            <Link to="/app/applications" className="appbar-icon" aria-label="Messages">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinejoin="round">
                <path d="M4.5 5h15A1.5 1.5 0 0 1 21 6.5v8A1.5 1.5 0 0 1 19.5 16H12l-4.5 3.6V16H4.5A1.5 1.5 0 0 1 3 14.5v-8A1.5 1.5 0 0 1 4.5 5z" />
              </svg>
            </Link>
            <NotificationBell />
            <Link to="/app/settings" className="venue-chip" title={venueName}>
              <span className="venue-chip-mark">{initials(venueName)}</span>
              <span className="venue-chip-copy">
                <span className="venue-chip-name">{venueName}</span>
                <VenueRatingBadge
                  average={rating.data?.avg_stars}
                  total={rating.data?.total_ratings}
                  loading={rating.isPending}
                  unavailable={rating.isError}
                />
              </span>
            </Link>
          </div>
        </header>

        <main className="main-content">
          <div className="content-wrapper"><Outlet /></div>
        </main>
      </div>

      <button
        type="button"
        className="sidebar-scrim"
        aria-hidden={!menuOpen}
        tabIndex={-1}
        onClick={() => setMenuOpen(false)}
      />
      <PostShiftRatingPrompt />
    </div>
  );
}
