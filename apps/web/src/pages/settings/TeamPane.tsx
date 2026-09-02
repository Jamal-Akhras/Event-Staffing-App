import { useState } from "react";

import { useToast } from "../../components/Toast";
import { useAuth } from "../../contexts/AuthContext";
import { initials } from "../../lib/useVenue";
import type { EmployedType, JoinCode } from "../../types/workforce";
import { RELATIONSHIP_LABELS } from "../../types/workforce";
import { Group, Tag, type SettingRow } from "./SettingsRows";
import { useJoinCodes } from "./useJoinCodes";

const TYPES: EmployedType[] = ["permanent", "part_time", "bank"];

function codeHint(code: JoinCode): string {
  const kind = RELATIONSHIP_LABELS[code.relationship_type];
  const role = code.default_role ? ` · ${code.default_role}` : "";
  return `${kind}${role} · used ${code.redeemed} of ${code.max_redemptions}`;
}

export function TeamPane({ venueName }: { venueName: string }) {
  const { user } = useAuth();
  const { toast } = useToast();
  const { codes, live, create, revoke } = useJoinCodes((type, message) => toast({ type, message }));
  const [type, setType] = useState<EmployedType>("permanent");
  const [role, setRole] = useState("");
  const [uses, setUses] = useState(1);

  const codeRows: SettingRow[] = live.map((code) => ({
    key: code.code,
    label: code.code,
    hint: codeHint(code),
    control: (
      <span className="st-inline">
        <button type="button" className="st-btn" onClick={() => navigator.clipboard?.writeText(code.code)}>
          Copy
        </button>
        <button type="button" className="st-btn" disabled={revoke.isPending} onClick={() => revoke.mutate(code.code)}>
          Turn off
        </button>
      </span>
    ),
  }));

  return (
    <>
      <Group
        title="Join codes"
        hint="Give a code to staff you already employ so they can add themselves to this venue. Flexible workers join your pool after they have worked a shift, not with a code."
        rows={[
          ...codeRows,
          {
            key: "new",
            label: codes.isLoading ? "Loading codes…" : "Create a code",
            hint: "Choose what the code makes someone, and how many people can use it",
            stack: true,
            control: (
              <span className="st-inline">
                <select
                  className="st-select"
                  value={type}
                  aria-label="Relationship"
                  onChange={(event) => setType(event.target.value as EmployedType)}
                >
                  {TYPES.map((item) => (
                    <option key={item} value={item}>{RELATIONSHIP_LABELS[item]}</option>
                  ))}
                </select>
                <input
                  className="st-input"
                  value={role}
                  placeholder="Role (optional)"
                  aria-label="Default role"
                  onChange={(event) => setRole(event.target.value)}
                />
                <input
                  className="st-input short"
                  type="number"
                  min={1}
                  max={500}
                  value={uses}
                  aria-label="How many people can use it"
                  onChange={(event) => setUses(Math.max(1, Number(event.target.value) || 1))}
                />
                <button
                  type="button"
                  className="st-btn primary"
                  disabled={create.isPending}
                  onClick={() =>
                    create.mutate({
                      relationship_type: type,
                      default_role: role.trim() || null,
                      max_redemptions: uses,
                    })
                  }
                >
                  {create.isPending ? "Creating…" : "Create"}
                </button>
              </span>
            ),
          },
        ]}
      />
      <Group
        title="Managers"
        hint="Owners control billing and deletion. Managers run the rota."
        soon
        rows={[
          {
            key: "owner",
            label: user?.email ?? "You",
            hint: "Owner · you",
            control: <Tag tone="live">Owner</Tag>,
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
