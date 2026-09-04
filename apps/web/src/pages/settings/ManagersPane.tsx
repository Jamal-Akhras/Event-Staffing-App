import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useToast } from "../../components/Toast";
import { deleteJson, fetchJson, postJson } from "../../lib/api";
import { Group, type SettingRow } from "./SettingsRows";

type Member = {
  user_id: string;
  email: string | null;
  role: string;
  venue_ids: string[] | null;
};

type Invitation = {
  invitation_id: string;
  email: string;
  role: string;
  token: string;
};

type VenueSummary = {
  venue_id: string;
  name: string;
};

const KEY = ["organisation-members"];

export function ManagersPane() {
  const { toast } = useToast();
  const client = useQueryClient();
  const members = useQuery({
    queryKey: KEY,
    queryFn: () => fetchJson<Member[]>("/organisations/me/members"),
  });
  const venues = useQuery({
    queryKey: ["my-venues"],
    queryFn: () => fetchJson<VenueSummary[]>("/venues"),
  });
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"admin" | "manager">("manager");
  const [venueIds, setVenueIds] = useState<string[]>([]);
  const [lastToken, setLastToken] = useState<string | null>(null);

  const invite = useMutation({
    mutationFn: () =>
      postJson<Invitation>("/organisations/me/members/invite", {
        email,
        role,
        venue_ids: role === "manager" ? venueIds : null,
      }),
    onSuccess: (invitation) => {
      setLastToken(invitation.token);
      setEmail("");
      setVenueIds([]);
      toast({ type: "success", message: "Invitation created." });
    },
    onError: (error: Error) => toast({ type: "error", message: error.message }),
  });

  const remove = useMutation({
    mutationFn: (userId: string) => deleteJson(`/organisations/me/members/${userId}`),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: KEY });
      toast({ type: "success", message: "Member removed." });
    },
    onError: (error: Error) => toast({ type: "error", message: error.message }),
  });

  const venueName = (venueId: string) =>
    venues.data?.find((venue) => venue.venue_id === venueId)?.name ?? venueId;

  const memberRows: SettingRow[] = (members.data ?? []).map((member) => ({
    key: member.user_id,
    label: member.email ?? member.user_id,
    hint:
      member.role +
      (member.venue_ids ? ` · ${member.venue_ids.map(venueName).join(", ")}` : " · all venues"),
    control: (
      <button
        type="button"
        className="st-btn"
        disabled={remove.isPending}
        onClick={() => remove.mutate(member.user_id)}
      >
        Remove
      </button>
    ),
  }));

  const inviteRows: SettingRow[] = [
    {
      key: "email",
      label: "Email",
      control: (
        <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="them@venue.co.uk" />
      ),
    },
    {
      key: "role",
      label: "Role",
      hint: role === "admin" ? "Everything except managing members" : "Day-to-day running of chosen venues",
      control: (
        <select value={role} onChange={(event) => setRole(event.target.value as "admin" | "manager")}>
          <option value="manager">Manager</option>
          <option value="admin">Admin</option>
        </select>
      ),
    },
    ...(role === "manager"
      ? [
          {
            key: "venues",
            label: "Venues",
            control: (
              <select
                multiple
                value={venueIds}
                onChange={(event) =>
                  setVenueIds(Array.from(event.target.selectedOptions, (option) => option.value))
                }
              >
                {(venues.data ?? []).map((venue) => (
                  <option key={venue.venue_id} value={venue.venue_id}>
                    {venue.name}
                  </option>
                ))}
              </select>
            ),
          } satisfies SettingRow,
        ]
      : []),
    {
      key: "send",
      label: "Create invitation",
      hint: lastToken ? `Share this code: ${lastToken}` : "They join at /join-team with the code",
      control: (
        <button
          type="button"
          className="st-btn"
          disabled={invite.isPending || !email || (role === "manager" && venueIds.length === 0)}
          onClick={() => invite.mutate()}
        >
          Invite
        </button>
      ),
    },
  ];

  return (
    <>
      <Group title="People with access" rows={memberRows} />
      <Group title="Invite someone" rows={inviteRows} />
    </>
  );
}
