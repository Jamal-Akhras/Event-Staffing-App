import { useState } from "react";

import { WEEKDAYS, readWeekStart, saveWeekStart } from "../../lib/weekStart";
import { Group, Switch, Tag } from "./SettingsRows";

const ROLES = ["Bartender", "Server", "Barback", "Host"];

export function SchedulingPane() {
  const [weekStart, setWeekStart] = useState(readWeekStart);

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
