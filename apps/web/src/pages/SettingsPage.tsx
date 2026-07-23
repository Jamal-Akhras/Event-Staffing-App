import { useEffect, useRef, useState } from "react";

import { ErrorCard } from "../components/ErrorCard";
import { LocationAutocomplete } from "../components/LocationAutocomplete";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { useAuth } from "../contexts/AuthContext";
import { API_BASE, fetchJson, putJson, uploadFile } from "../lib/api";
import "./SettingsPage.css";

type AccountData = {
  account_id: string;
  name: string;
  country: string;
  currency: string;
  venue_type: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  default_location: string | null;
  avatar_url: string | null;
  photos: string[];
  notification_preferences: NotifPrefs;
};

type NotifPrefs = {
  new_applications: boolean;
  shift_reminders: boolean;
  no_show_alerts: boolean;
};

const DEFAULT_NOTIF_PREFS: NotifPrefs = { new_applications: true, shift_reminders: true, no_show_alerts: true };

const NOTIF_OPTIONS = [
  ["new_applications", "New Applications", "When workers apply to your shifts"],
  ["shift_reminders", "Shift Reminders", "Upcoming shifts requiring attention"],
  ["no_show_alerts", "No-Show Alerts", "When workers don't check in on time"],
] as const;

type SectionKey = "profile" | "contact" | "photos" | "notifications";

export function SettingsPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [expanded, setExpanded] = useState<Record<SectionKey, boolean>>({
    profile: false, contact: false, photos: false, notifications: true,
  });
  const toggle = (k: SectionKey) => setExpanded((prev) => ({ ...prev, [k]: !prev[k] }));

  const [account, setAccount] = useState<AccountData | null>(null);
  const [name, setName] = useState("");
  const [venueType, setVenueType] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [defaultLocation, setDefaultLocation] = useState("");
  const [photos, setPhotos] = useState<string[]>([]);
  const [notifs, setNotifs] = useState<NotifPrefs>(DEFAULT_NOTIF_PREFS);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved">("idle");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const avatarInputRef = useRef<HTMLInputElement>(null);
  const photoInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!user?.account_id) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchJson<AccountData>("/accounts/me")
      .then((data) => {
        setAccount(data);
        setName(data.name ?? "");
        setVenueType(data.venue_type ?? "");
        setContactEmail(data.contact_email ?? "");
        setContactPhone(data.contact_phone ?? "");
        setDefaultLocation(data.default_location ?? "");
        setPhotos(data.photos ?? []);
        setNotifs(data.notification_preferences ?? DEFAULT_NOTIF_PREFS);
      })
      .catch((err: Error) => {
        toast({ type: "error", message: err.message });
        setLoadError(err.message);
      })
      .finally(() => setLoading(false));
  }, [user?.account_id]);

  const save = async () => {
    setSaveStatus("saving");
    try {
      const updated = await putJson<AccountData>("/accounts/me", {
        name: name || undefined,
        venue_type: venueType || undefined,
        contact_email: contactEmail || undefined,
        contact_phone: contactPhone || undefined,
        default_location: defaultLocation || undefined,
        photos,
        notification_preferences: notifs,
      });
      setAccount(updated);
      setNotifs(updated.notification_preferences ?? DEFAULT_NOTIF_PREFS);
      setSaveStatus("saved");
      toast({ type: "success", message: "Settings saved." });
      setTimeout(() => setSaveStatus("idle"), 2500);
    } catch (err) {
      setSaveStatus("idle");
      toast({ type: "error", message: (err as Error).message });
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !account) return;
    setUploading(true);
    try {
      const result = await uploadFile<{ url: string }>("/uploads/venue-avatar", file);
      setAccount({ ...account, avatar_url: result.url });
      toast({ type: "success", message: "Logo uploaded." });
    } catch (err) {
      toast({ type: "error", message: (err as Error).message });
    } finally {
      setUploading(false);
      if (avatarInputRef.current) avatarInputRef.current.value = "";
    }
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadFile<{ url: string }>("/uploads/venue-photo", file);
      setPhotos((prev) => [...prev, result.url]);
      toast({ type: "success", message: "Photo uploaded." });
    } catch (err) {
      toast({ type: "error", message: (err as Error).message });
    } finally {
      setUploading(false);
      if (photoInputRef.current) photoInputRef.current.value = "";
    }
  };

  const removePhoto = (url: string) => setPhotos((prev) => prev.filter((p) => p !== url));
  const initials = name ? name.slice(0, 2).toUpperCase() : "VN";
  const avatarSrc = account?.avatar_url ? `${API_BASE}${account.avatar_url}` : null;
  const initialLoading = loading && !account && !loadError;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Manage your venue profile, photos and preferences.</p>
        </div>
      </div>

      {initialLoading && (
        <div className="settings-grid">
          <SkeletonCard className="settings-skeleton-card tall" lines={6} />
          <SkeletonCard className="settings-skeleton-card" lines={4} />
          <SkeletonCard className="settings-skeleton-card" lines={4} />
          <SkeletonCard className="settings-skeleton-card tall" lines={6} />
        </div>
      )}
      {!initialLoading && loadError && <ErrorCard message={loadError} />}

      {!initialLoading && !loadError && <div className="settings-grid">
        <div className="settings-col">

          <div className="card settings-accordion-card">
            <button className="settings-card-header" onClick={() => toggle("profile")} aria-expanded={expanded.profile}>
              <div>
                <h2 className="settings-section-title">Venue Profile</h2>
                <p className="settings-section-desc">Your public identity shown to workers browsing shifts.</p>
              </div>
              <span className={`settings-chevron${expanded.profile ? " open" : ""}`} />
            </button>
            <div className={`settings-card-body${expanded.profile ? " open" : ""}`}>
              <div className="settings-card-inner">
                <div className="avatar-center">
                  {avatarSrc ? <img src={avatarSrc} alt="Venue logo" className="avatar-circle" /> : <div className="avatar-placeholder">{initials}</div>}
                  <button className="btn secondary" style={{ fontSize: "0.85rem", padding: "8px 18px" }} disabled={uploading} onClick={() => avatarInputRef.current?.click()}>
                    {uploading ? "Uploading…" : "Change logo"}
                  </button>
                  <span className="avatar-hint">JPG, PNG or WebP · max 10 MB</span>
                  <input ref={avatarInputRef} type="file" accept="image/*" style={{ display: "none" }} onChange={handleAvatarUpload} />
                </div>
                <div className="form">
                  <label className="settings-label"><span>Venue Name <i className="info-icon">i</i></span><input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. The Pearl Bar" /></label>
                  <label className="settings-label">
                    <span>Venue Type <i className="info-icon">i</i></span>
                    <select value={venueType} onChange={(e) => setVenueType(e.target.value)}>
                      <option value="">Select type…</option>
                      <option>Restaurant & Bar</option><option>Hotel</option><option>Event Venue</option>
                      <option>Catering</option><option>Conference Center</option><option>Other</option>
                    </select>
                  </label>
                  <label className="settings-label"><span>Default Location <i className="info-icon">i</i></span><LocationAutocomplete value={defaultLocation} onChange={setDefaultLocation} placeholder="e.g. 12 King St, London" /></label>
                </div>
              </div>
            </div>
          </div>

          <div className="card settings-accordion-card">
            <button className="settings-card-header" onClick={() => toggle("contact")} aria-expanded={expanded.contact}>
              <div>
                <h2 className="settings-section-title">Contact Information</h2>
                <p className="settings-section-desc">Used for direct operational communications.</p>
              </div>
              <span className={`settings-chevron${expanded.contact ? " open" : ""}`} />
            </button>
            <div className={`settings-card-body${expanded.contact ? " open" : ""}`}>
              <div className="settings-card-inner">
                <div className="form">
                  <label className="settings-label"><span>Contact Email <i className="info-icon">i</i></span><input type="email" value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} placeholder="manager@venue.com" /></label>
                  <label className="settings-label"><span>Phone Number <i className="info-icon">i</i></span><input type="tel" value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} placeholder="+44 7700 900000" /></label>
                </div>
              </div>
            </div>
          </div>

        </div>
        <div className="settings-col">

          <div className="card settings-accordion-card">
            <button className="settings-card-header" onClick={() => toggle("photos")} aria-expanded={expanded.photos}>
              <div>
                <h2 className="settings-section-title">Venue Photos</h2>
                <p className="settings-section-desc">Shown on your profile when workers browse and apply.</p>
              </div>
              <span className={`settings-chevron${expanded.photos ? " open" : ""}`} />
            </button>
            <div className={`settings-card-body${expanded.photos ? " open" : ""}`}>
              <div className="settings-card-inner">
                <div className="photo-grid">
                  {photos.map((url) => (
                    <div key={url} className="photo-item">
                      <img src={url.startsWith("/uploads") ? `${API_BASE}${url}` : url} alt="" />
                      <button className="photo-remove" onClick={() => removePhoto(url)} title="Remove">✕</button>
                    </div>
                  ))}
                  <button className="photo-add" disabled={uploading} onClick={() => photoInputRef.current?.click()}>
                    <span className="photo-add-icon">+</span>
                    <span>{uploading ? "Uploading…" : "Add photo"}</span>
                  </button>
                </div>
                <input ref={photoInputRef} type="file" accept="image/*" style={{ display: "none" }} onChange={handlePhotoUpload} />
              </div>
            </div>
          </div>

          <div className="card settings-accordion-card">
            <button className="settings-card-header" onClick={() => toggle("notifications")} aria-expanded={expanded.notifications}>
              <div>
                <h2 className="settings-section-title">Notifications</h2>
                <p className="settings-section-desc">Choose which activity triggers an alert. Email delivery activates with our next release.</p>
              </div>
              <span className={`settings-chevron${expanded.notifications ? " open" : ""}`} />
            </button>
            <div className={`settings-card-body${expanded.notifications ? " open" : ""}`}>
              <div className="settings-card-inner">
                <p className="notif-subheader">Notification Preferences</p>
                <div className="notif-pending-note" role="note">
                  Your choices are saved now and will be honoured automatically once email delivery is enabled.
                </div>
                <div className="notif-list">
                  {NOTIF_OPTIONS.map(([key, label, desc], i) => (
                    <>
                      {i > 0 && <hr key={`sep-${key}`} className="notif-sep" />}
                      <label key={key} className="toggle-row">
                        <div className="toggle-label">
                          <strong>{label}</strong>
                          <span>{desc}</span>
                        </div>
                        <div className="toggle-switch">
                          <input type="checkbox" checked={notifs[key]} onChange={() => setNotifs({ ...notifs, [key]: !notifs[key] })} />
                          <span className="toggle-slider" />
                        </div>
                      </label>
                    </>
                  ))}
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>}

      {!initialLoading && !loadError && <div className="settings-save-bar">
        <button className="btn primary" style={{ minWidth: 140 }} disabled={saveStatus === "saving"} onClick={save}>
          {saveStatus === "saving" ? "Saving…" : saveStatus === "saved" ? "Saved ✓" : "Save changes"}
        </button>
        {saveStatus === "saved" && <span className="settings-save-msg">All changes saved successfully.</span>}
      </div>}
    </div>
  );
}
