import { MarketingIcon } from "./MarketingIcon";
import "./ProductPreview.css";

export function WorkerPhonePreview({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`worker-phone ${compact ? "compact" : ""}`} aria-label="Worker app preview">
      <div className="phone-topbar"><span /><strong>9:41</strong><span /></div>
      <div className="phone-appbar">
        <div><small>Good afternoon</small><strong>Find your next shift</strong></div>
        <span className="phone-avatar">AM</span>
      </div>
      <div className="phone-filter-row">
        <span>Bath</span><span>Hospitality</span><span>This week</span>
      </div>
      <article className="shift-preview-card">
        <div className="shift-card-cover">
          <span className="shift-live-pill">Good match</span>
          <span className="shift-cover-mark">N</span>
        </div>
        <div className="shift-card-body">
          <div className="shift-title-row">
            <div><small>Northgate House</small><h3>Event bartender</h3></div>
            <strong>£13.50<small>/hr</small></strong>
          </div>
          <div className="shift-meta"><MarketingIcon name="calendar" size={15} /> Fri 28 Aug · 18:00–00:00</div>
          <div className="shift-meta"><MarketingIcon name="location" size={15} /> Bath · 0.7 miles away</div>
          <div className="shift-card-footer">
            <span><i /> Reliable venue</span>
            <button type="button">View shift</button>
          </div>
        </div>
      </article>
      <div className="phone-nav"><b>⌂</b><span>Shifts</span><span>Messages</span><span>Profile</span></div>
    </div>
  );
}

export function VenueDashboardPreview({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`venue-preview ${compact ? "compact" : ""}`} aria-label="Venue dashboard preview">
      <aside className="venue-preview-sidebar">
        <span className="venue-mini-logo">V</span>
        {Array.from({ length: 6 }, (_, index) => <i key={index} className={index === 0 ? "active" : ""} />)}
      </aside>
      <div className="venue-preview-main">
        <div className="venue-preview-head">
          <div><small>Friday, 28 August</small><strong>Overview</strong></div>
          <button type="button">+ Post shift</button>
        </div>
        <div className="venue-metrics">
          <article><small>Open seats</small><strong>3</strong><span>Needs attention</span></article>
          <article><small>Applications</small><strong>12</strong><span>Ready to review</span></article>
          <article><small>Fill rate</small><strong>92%</strong><span>Last 30 days</span></article>
        </div>
        <article className="venue-roster-card">
          <div className="venue-card-head"><strong>Tonight's team</strong><span>View schedule</span></div>
          {[
            ["AM", "Alex Morgan", "Bartender", "18:00"],
            ["JT", "Jamie Taylor", "Waiting staff", "18:30"],
            ["SK", "Sam Khan", "Bar back", "19:00"],
          ].map(([initials, name, role, time]) => (
            <div className="venue-roster-row" key={name}>
              <span className="roster-avatar">{initials}</span>
              <div><strong>{name}</strong><small>{role}</small></div>
              <time>{time}</time><b>Confirmed</b>
            </div>
          ))}
        </article>
      </div>
    </div>
  );
}
