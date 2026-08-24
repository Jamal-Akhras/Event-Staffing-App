import { useEffect, useState } from "react";

import { useToast } from "../../components/Toast";
import {
  fetchNotificationPreferences,
  saveNotificationPreferences,
  type NotificationPreferences,
} from "../../lib/notificationsApi";

const CHANNEL_OPTIONS = [
  ["in_app", "In-App", "Show alerts in the dashboard notification bell"],
  ["email", "Email", "Send a copy of important updates to your inbox"],
  ["push", "Push", "Mobile push alerts, active once the app enables them"],
] as const;

const CATEGORY_OPTIONS = [
  ["applications", "Applications", "When workers apply or withdraw"],
  ["shift_changes", "Shift Changes", "Edits, closures and cancellations"],
  ["messages", "Messages", "New messages from workers"],
  ["reminders", "Reminders", "Upcoming shifts requiring attention"],
  ["attendance", "Attendance", "Check-ins, check-outs and no-shows"],
] as const;

type NotificationsCardProps = {
  expanded: boolean;
  onToggleExpanded: () => void;
};

export function NotificationsCard({ expanded, onToggleExpanded }: NotificationsCardProps) {
  const { toast } = useToast();
  const [prefs, setPrefs] = useState<NotificationPreferences | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    setLoadError(null);
    fetchNotificationPreferences()
      .then(setPrefs)
      .catch((err: Error) => setLoadError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const applyChange = (next: NotificationPreferences, previous: NotificationPreferences) => {
    if (saving) return;
    setSaving(true);
    setPrefs(next);
    saveNotificationPreferences(next)
      .then(setPrefs)
      .catch((err: Error) => {
        setPrefs(previous);
        toast({ type: "error", message: err.message });
      })
      .finally(() => setSaving(false));
  };

  const toggleChannel = (key: keyof NotificationPreferences["channels"]) => {
    if (!prefs) return;
    applyChange(
      { ...prefs, channels: { ...prefs.channels, [key]: !prefs.channels[key] } },
      prefs
    );
  };

  const toggleCategory = (key: keyof NotificationPreferences["categories"]) => {
    if (!prefs) return;
    applyChange(
      { ...prefs, categories: { ...prefs.categories, [key]: !prefs.categories[key] } },
      prefs
    );
  };

  return (
    <div className="card settings-accordion-card">
      <button className="settings-card-header" onClick={onToggleExpanded} aria-expanded={expanded}>
        <div>
          <h2 className="settings-section-title">Notifications</h2>
          <p className="settings-section-desc">Choose how and when we alert you. Changes save automatically.</p>
        </div>
        <span className={`settings-chevron${expanded ? " open" : ""}`} />
      </button>
      <div className={`settings-card-body${expanded ? " open" : ""}`}>
        <div className="settings-card-inner">
          {loading && <p className="notif-subheader">Loading preferences…</p>}
          {!loading && loadError && (
            <div>
              <p className="notif-subheader" style={{ color: "var(--danger-500)" }}>{loadError}</p>
              <button type="button" className="btn secondary" onClick={load}>Try again</button>
            </div>
          )}
          {!loading && !loadError && prefs && (
            <>
              <p className="notif-subheader">Delivery Channels</p>
              <div className="notif-list">
                {CHANNEL_OPTIONS.map(([key, label, desc], i) => (
                  <ToggleRow
                    key={key}
                    checked={prefs.channels[key]}
                    desc={desc}
                    label={label}
                    disabled={saving}
                    withSeparator={i > 0}
                    onChange={() => toggleChannel(key)}
                  />
                ))}
              </div>
              <p className="notif-subheader" style={{ marginTop: 18 }}>Categories</p>
              <div className="notif-list">
                {CATEGORY_OPTIONS.map(([key, label, desc], i) => (
                  <ToggleRow
                    key={key}
                    checked={prefs.categories[key]}
                    desc={desc}
                    label={label}
                    disabled={saving}
                    withSeparator={i > 0}
                    onChange={() => toggleCategory(key)}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function ToggleRow({
  checked,
  desc,
  label,
  disabled,
  withSeparator,
  onChange,
}: {
  checked: boolean;
  desc: string;
  label: string;
  disabled: boolean;
  withSeparator: boolean;
  onChange: () => void;
}) {
  return (
    <>
      {withSeparator && <hr className="notif-sep" />}
      <label className="toggle-row">
        <div className="toggle-label">
          <strong>{label}</strong>
          <span>{desc}</span>
        </div>
        <div className="toggle-switch">
          <input type="checkbox" checked={checked} disabled={disabled} onChange={onChange} />
          <span className="toggle-slider" />
        </div>
      </label>
    </>
  );
}
