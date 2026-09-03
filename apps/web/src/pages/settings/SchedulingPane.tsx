import { useState } from "react";

import { WEEKDAYS, readWeekStart, saveWeekStart } from "../../lib/weekStart";
import { Group, Switch, Tag } from "./SettingsRows";
import type { VenueSettings } from "./useVenueSettings";

const ROLES = ["Bartender", "Server", "Barback", "Host"];

export function SchedulingPane({ settings }: { settings: VenueSettings }) {
  const [weekStart, setWeekStart] = useState(readWeekStart);
  const draft = settings.draft;

  const changeWeekStart = (day: number) => {
    saveWeekStart(day);
    setWeekStart(day);
  };

  return (
    <>
      <Group
        title="Board"
        rows={[
          {
            key: "week-start",
            label: "Week starts on",
            hint: "How the Shifts board lays out the week",
            control: (
              <>
                <select className="st-select" value={weekStart} onChange={(event) => changeWeekStart(Number(event.target.value))}>
                  {WEEKDAYS.map((name, day) => <option key={name} value={day}>{name}</option>)}
                </select>
                <Tag tone="live">Saved</Tag>
              </>
            ),
          },
        ]}
      />
      <Group
        title="Filling gaps"
        hint="An unfilled or dropped shift goes to your own people first, then the open market. You control both steps."
        rows={[
          {
            key: "named-hold",
            label: "A named person holds it",
            hint:
              draft?.named_offer_hours === null
                ? "Waits for their answer - the shift never moves on by itself"
                : `An assigned shift moves on after ${draft?.named_offer_hours ?? 24} hours without an answer`,
            control: (
              <span className="st-inline">
                <Switch
                  checked={draft?.named_offer_hours !== null}
                  label="Move on from an unanswered offer"
                  onChange={() =>
                    settings.update({ named_offer_hours: draft?.named_offer_hours === null ? 24 : null })
                  }
                />
                {draft?.named_offer_hours !== null && (
                  <select
                    className="st-select"
                    value={draft?.named_offer_hours ?? 24}
                    aria-label="Named offer hold in hours"
                    onChange={(event) => settings.update({ named_offer_hours: Number(event.target.value) })}
                  >
                    {[4, 12, 24, 48, 72].map((hours) => (
                      <option key={hours} value={hours}>{hours} hours</option>
                    ))}
                  </select>
                )}
              </span>
            ),
          },
          {
            key: "team-window",
            label: "Then your employed team",
            hint:
              draft?.team_hours === null
                ? "Off - unfilled shifts skip straight to your pool"
                : `Employed staff see it ${draft?.team_hours ?? 6} hours before the pool`,
            control: (
              <span className="st-inline">
                <Switch
                  checked={draft?.team_hours !== null}
                  label="Offer to employed staff first"
                  onChange={() => settings.update({ team_hours: draft?.team_hours === null ? 6 : null })}
                />
                {draft?.team_hours !== null && (
                  <select
                    className="st-select"
                    value={draft?.team_hours ?? 6}
                    aria-label="Team window in hours"
                    onChange={(event) => settings.update({ team_hours: Number(event.target.value) })}
                  >
                    {[2, 4, 6, 12, 24].map((hours) => (
                      <option key={hours} value={hours}>{hours} hours</option>
                    ))}
                  </select>
                )}
              </span>
            ),
          },
          {
            key: "pool-window",
            label: "Then your pool",
            hint:
              draft?.pool_hours === null
                ? "Off - new shifts go straight to the open market"
                : `Your team and pool see a shift ${draft?.pool_hours ?? 24} hours before anyone else`,
            control: (
              <span className="st-inline">
                <Switch
                  checked={draft?.pool_hours !== null}
                  label="Offer to your people first"
                  onChange={() => settings.update({ pool_hours: draft?.pool_hours === null ? 24 : null })}
                />
                {draft?.pool_hours !== null && (
                  <select
                    className="st-select"
                    value={draft?.pool_hours ?? 24}
                    aria-label="Pool window in hours"
                    onChange={(event) => settings.update({ pool_hours: Number(event.target.value) })}
                  >
                    {[4, 12, 24, 48, 72].map((hours) => (
                      <option key={hours} value={hours}>{hours} hours</option>
                    ))}
                  </select>
                )}
              </span>
            ),
          },
          {
            key: "market-lead",
            label: "Open market safety net",
            hint:
              draft?.market_lead_hours === null
                ? "Off - shifts never reach the open market on their own"
                : `Unfilled shifts reach the open market no later than ${draft?.market_lead_hours ?? 48} hours before they start`,
            control: (
              <span className="st-inline">
                <Switch
                  checked={draft?.market_lead_hours !== null}
                  label="Publish to the open market automatically"
                  onChange={() =>
                    settings.update({ market_lead_hours: draft?.market_lead_hours === null ? 48 : null })
                  }
                />
                {draft?.market_lead_hours !== null && (
                  <select
                    className="st-select"
                    value={draft?.market_lead_hours ?? 48}
                    aria-label="Market lead time in hours"
                    onChange={(event) => settings.update({ market_lead_hours: Number(event.target.value) })}
                  >
                    {[12, 24, 48, 72, 96].map((hours) => (
                      <option key={hours} value={hours}>{hours} hours</option>
                    ))}
                  </select>
                )}
              </span>
            ),
          },
        ]}
      />
      <Group
        title="Posting defaults"
        hint="Pre-filled on every new shift so posting takes seconds."
        soon
        rows={[
          { key: "roles", label: "Roles you hire", control: <span className="st-chips">{ROLES.map((role) => <span key={role}>{role}</span>)}</span> },
          { key: "pay", label: "Pay per role", hint: "£ per hour, editable per shift", control: <span className="st-readonly">Bartender 14.50 · Server 13.50</span> },
          { key: "length", label: "Shift length", control: <><input className="st-input short" defaultValue="5.5" /> <span className="st-readonly">hours</span></> },
          { key: "notes", label: "House notes", hint: "Added to every shift: dress code, entrance, who to ask for", stack: true, control: <textarea className="st-textarea" rows={2} defaultValue="Black shirt and trousers, non-slip shoes." /> },
        ]}
      />
      <Group
        title="Hiring rules"
        hint="Decide once; applied to every shift."
        soon
        rows={[
          { key: "auto", label: "Auto-approve regulars", hint: "Three or more completed shifts with you", control: <Switch checked disabled label="Auto-approve regulars" onChange={() => undefined} /> },
          { key: "first", label: "Regulars-first window", hint: "Regulars see new shifts before everyone else", control: <select className="st-select" defaultValue="1 hour"><option>Off</option><option>1 hour</option><option>4 hours</option><option>24 hours</option></select> },
          { key: "close", label: "Close applications", hint: "Before the shift starts", control: <select className="st-select" defaultValue="2 hours before"><option>2 hours before</option><option>6 hours before</option><option>The day before</option></select> },
          { key: "notice", label: "Cancellation notice", hint: "Later cancellations count against reliability", control: <select className="st-select" defaultValue="24 hours"><option>12 hours</option><option>24 hours</option><option>48 hours</option></select> },
        ]}
      />
    </>
  );
}
