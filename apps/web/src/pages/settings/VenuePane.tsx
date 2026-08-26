import { useRef } from "react";

import { LocationAutocomplete } from "../../components/LocationAutocomplete";
import { MarketSelect } from "../../components/MarketSelect";
import { API_BASE } from "../../lib/api";
import { useMarkets } from "../../lib/useMarkets";
import { initials } from "../../lib/useVenue";
import { Group } from "./SettingsRows";
import type { VenueSettings } from "./useVenueSettings";

const VENUE_TYPES = ["Restaurant & bar", "Hotel", "Event venue", "Catering", "Conference centre", "Other"];

function mediaUrl(url: string) {
  return url.startsWith("/uploads") ? `${API_BASE}${url}` : url;
}

export function VenuePane({ settings }: { settings: VenueSettings }) {
  const { markets, loading, error, retry } = useMarkets();
  const logoInput = useRef<HTMLInputElement>(null);
  const photoInput = useRef<HTMLInputElement>(null);
  const { venue, draft, update, uploading } = settings;
  if (!venue || !draft) return null;

  return (
    <>
      <Group
        title="Profile"
        hint="What workers see when they browse your shifts."
        rows={[
          {
            key: "logo",
            label: "Logo",
            hint: "Square, JPG/PNG/WebP up to 10 MB",
            control: (
              <>
                {venue.avatar_url ? (
                  <img className="st-avatar" src={mediaUrl(venue.avatar_url)} alt="" />
                ) : (
                  <span className="st-avatar">{initials(draft.name || "V")}</span>
                )}
                <button type="button" className="st-btn" disabled={uploading} onClick={() => logoInput.current?.click()}>
                  {uploading ? "Uploading…" : "Change"}
                </button>
                <input ref={logoInput} type="file" accept="image/*" hidden onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) settings.uploadLogo(file);
                  event.target.value = "";
                }} />
              </>
            ),
          },
          { key: "name", label: "Name", control: <input className="st-input" value={draft.name} onChange={(event) => update({ name: event.target.value })} /> },
          {
            key: "type",
            label: "Type",
            control: (
              <select className="st-select" value={draft.venue_type} onChange={(event) => update({ venue_type: event.target.value })}>
                <option value="">Choose…</option>
                {VENUE_TYPES.map((type) => <option key={type}>{type}</option>)}
              </select>
            ),
          },
          {
            key: "city",
            label: "City",
            hint: "Shifts only reach workers in this market",
            control: <MarketSelect markets={markets} loading={loading} error={error} value={draft.market_id} onChange={(market_id) => update({ market_id })} onRetry={retry} country={venue.country} />,
          },
          {
            key: "address",
            label: "Address",
            hint: "Default for new shifts; revealed to workers once booked",
            stack: true,
            control: <LocationAutocomplete value={draft.default_location} onChange={(default_location) => update({ default_location })} placeholder="12 Kingsmead Square, Bath" />,
          },
          {
            key: "photos",
            label: "Photos",
            hint: `${draft.photos.length} of 20 · the first is your cover`,
            stack: true,
            control: (
              <div className="st-photos">
                {draft.photos.map((url) => (
                  <div key={url} className="st-photo">
                    <img src={mediaUrl(url)} alt="" />
                    <button type="button" aria-label="Remove photo" onClick={() => update({ photos: draft.photos.filter((photo) => photo !== url) })}>×</button>
                  </div>
                ))}
                <button type="button" className="st-photo-add" disabled={uploading || draft.photos.length >= 20} onClick={() => photoInput.current?.click()}>+</button>
                <input ref={photoInput} type="file" accept="image/*" hidden onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) settings.uploadPhoto(file);
                  event.target.value = "";
                }} />
              </div>
            ),
          },
          {
            key: "country",
            label: "Country & currency",
            hint: "Set at registration · ask us to change it",
            control: <span className="st-readonly">{venue.country} · {venue.currency}</span>,
          },
        ]}
      />
      <Group
        title="Contact"
        hint="For shift-day calls. Only booked workers see it."
        rows={[
          { key: "email", label: "Email", control: <input className="st-input" type="email" value={draft.contact_email} onChange={(event) => update({ contact_email: event.target.value })} placeholder="manager@venue.com" /> },
          { key: "phone", label: "Phone", control: <input className="st-input" type="tel" value={draft.contact_phone} onChange={(event) => update({ contact_phone: event.target.value })} placeholder="+44 7700 900000" /> },
        ]}
      />
    </>
  );
}
