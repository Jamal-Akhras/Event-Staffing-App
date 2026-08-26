import { useAuth } from "../../contexts/AuthContext";
import { initials } from "../../lib/useVenue";
import { Group } from "./SettingsRows";

export function TeamPane({ venueName }: { venueName: string }) {
  const { user } = useAuth();
  return (
    <>
      <Group
        title="People"
        hint="Owners control billing and deletion. Managers run the rota."
        soon
        rows={[
          {
            key: "owner",
            label: user?.email ?? "You",
            hint: "Owner · you",
            control: <span className="st-role">Owner</span>,
          },
          {
            key: "invite",
            label: "Invite a colleague",
            hint: "They get an email and choose a password",
            stack: true,
            control: (
              <span className="st-inline">
                <input className="st-input" placeholder="colleague@venue.com" />
                <select className="st-select" defaultValue="Manager"><option>Manager</option><option>Owner</option></select>
                <button type="button" className="st-btn primary">Invite</button>
              </span>
            ),
          },
        ]}
      />
      <Group
        title="Venues"
        hint="Each venue has its own shifts, workers and settings."
        soon
        rows={[
          { key: "venue", label: venueName, hint: "Active", control: <span className="st-avatar small">{initials(venueName)}</span> },
          { key: "add", label: "Add a venue", control: <button type="button" className="st-btn">+ Add</button> },
        ]}
      />
    </>
  );
}
