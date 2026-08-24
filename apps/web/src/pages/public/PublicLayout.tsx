import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";

import { MarketingIcon } from "./MarketingIcon";
import "./PublicLayout.css";

const NAV_ITEMS = [
  { to: "/for-workers", label: "Find shifts" },
  { to: "/for-employers", label: "Find staff" },
  { to: "/safety", label: "Trust & safety" },
] as const;

export function Brand({ light = false }: { light?: boolean }) {
  return (
    <Link className={`public-brand ${light ? "light" : ""}`} to="/" aria-label="Venue OS home">
      <span className="public-brand-mark">V</span>
      <span>Venue OS</span>
    </Link>
  );
}

export function PublicLayout() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setIsOpen(false);
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [location.pathname]);

  return (
    <div className="public-site">
      <header className="public-header">
        <div className="public-nav-shell">
          <Brand />
          <nav className={`public-nav ${isOpen ? "open" : ""}`} aria-label="Main navigation">
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to}>{item.label}</NavLink>
            ))}
            <Link className="public-mobile-login" to="/login">Venue login</Link>
            <Link className="public-mobile-cta" to="/register">Post a shift</Link>
          </nav>
          <div className="public-nav-actions">
            <Link className="public-login-link" to="/login">Log in</Link>
            <Link className="public-button dark small" to="/register">
              Post a shift
              <MarketingIcon name="arrow" size={17} />
            </Link>
          </div>
          <button
            className={`public-menu-button ${isOpen ? "open" : ""}`}
            type="button"
            aria-expanded={isOpen}
            aria-label={isOpen ? "Close navigation" : "Open navigation"}
            onClick={() => setIsOpen((value) => !value)}
          >
            <span /><span />
          </button>
        </div>
      </header>

      <main><Outlet /></main>

      <footer className="public-footer">
        <div className="public-footer-top">
          <div className="public-footer-brand">
            <Brand light />
            <p>Local hospitality staffing, built around reliable people and better shifts.</p>
            <span className="public-launch-pill">Launching in Bath</span>
          </div>
          <div className="public-footer-links">
            <div>
              <strong>Platform</strong>
              <Link to="/for-workers">For workers</Link>
              <Link to="/for-employers">For venues</Link>
              <Link to="/download">Get the app</Link>
            </div>
            <div>
              <strong>Company</strong>
              <Link to="/safety">Trust &amp; safety</Link>
              <Link to="/login">Venue login</Link>
              <Link to="/register">Create an account</Link>
            </div>
            <div>
              <strong>Legal</strong>
              <Link to="/terms">Terms</Link>
              <Link to="/privacy">Privacy</Link>
              <Link to="/cookies">Cookies</Link>
            </div>
          </div>
        </div>
        <div className="public-footer-bottom">
          <span>© 2026 Venue OS</span>
          <span>Built for the people behind great hospitality.</span>
        </div>
      </footer>
    </div>
  );
}
