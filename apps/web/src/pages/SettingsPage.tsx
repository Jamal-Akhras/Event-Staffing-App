import { useState } from "react";

import { ErrorCard } from "../components/ErrorCard";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { AccountPane } from "./settings/AccountPane";
import { BillingPane } from "./settings/BillingPane";
import { TeamPane } from "./settings/ComingSoonPanes";
import { NotificationsPane } from "./settings/NotificationsPane";
import { SchedulingPane } from "./settings/SchedulingPane";
import { SearchContext } from "./settings/SettingsRows";
import { VenuePane } from "./settings/VenuePane";
import { useVenueSettings } from "./settings/useVenueSettings";
import "./SettingsPage.css";

const TABS = [
  { key: "venue", label: "Venue" },
  { key: "scheduling", label: "Scheduling" },
  { key: "notifications", label: "Notifications" },
  { key: "team", label: "Team", soon: true },
  { key: "billing", label: "Billing" },
  { key: "account", label: "Account" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

export function SettingsPage() {
  const { toast } = useToast();
  const settings = useVenueSettings((type, message) => toast({ type, message }));
  const [tab, setTab] = useState<TabKey>("venue");
  const [query, setQuery] = useState("");
  const searching = query.trim().length > 0;

  if (settings.error) return <ErrorCard message={settings.error.message} />;
  if (settings.loading || !settings.draft) {
    return <div className="settings"><SkeletonCard lines={3} /><SkeletonCard lines={6} /></div>;
  }

  const panes: Record<TabKey, JSX.Element> = {
    venue: <VenuePane settings={settings} />,
    scheduling: <SchedulingPane />,
    notifications: <NotificationsPane />,
    team: <TeamPane venueName={settings.draft.name} />,
    billing: <BillingPane />,
    account: <AccountPane />,
  };

  return (
    <SearchContext.Provider value={query}>
      <div className="settings">
        <div className="st-head">
          <h1>Settings</h1>
          <label className="st-search">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></svg>
            <input value={query} placeholder="Search settings" onChange={(event) => setQuery(event.target.value)} />
            {query && <button type="button" aria-label="Clear search" onClick={() => setQuery("")}>×</button>}
          </label>
        </div>

        <div className={`st-tabs ${searching ? "muted" : ""}`} role="tablist">
          {TABS.map((item) => (
            <button key={item.key} type="button" role="tab" aria-selected={tab === item.key} className={tab === item.key ? "on" : ""} onClick={() => { setTab(item.key); setQuery(""); }}>
              {item.label}{"soon" in item && <small>soon</small>}
            </button>
          ))}
        </div>

        {searching ? (
          TABS.map((item) => (
            <div key={item.key} className="st-pane">
              <h3 className="st-pane-title">{item.label}</h3>
              {panes[item.key]}
            </div>
          ))
        ) : (
          <div className="st-pane">{panes[tab]}</div>
        )}

        {settings.dirty && (
          <div className="st-savebar">
            <span>Unsaved changes</span>
            <button type="button" className="st-btn" disabled={settings.saving} onClick={settings.discard}>Discard</button>
            <button type="button" className="st-btn primary" disabled={settings.saving} onClick={settings.save}>
              {settings.saving ? "Saving…" : "Save"}
            </button>
          </div>
        )}
      </div>
    </SearchContext.Provider>
  );
}
