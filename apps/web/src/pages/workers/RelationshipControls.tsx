import { useState } from "react";

import type { EmployedType } from "../../types/workforce";
import { RELATIONSHIP_LABELS } from "../../types/workforce";
import type { DirectoryEntry } from "./directory";
import type { useDirectory } from "./useDirectory";

const EMPLOYED: EmployedType[] = ["permanent", "part_time", "bank"];

type Props = {
  entry: DirectoryEntry;
  actions: ReturnType<typeof useDirectory>;
};

export function RelationshipControls({ entry, actions }: Props) {
  const [type, setType] = useState<EmployedType>("permanent");
  const busy =
    actions.addToPool.isPending ||
    actions.removeFromPool.isPending ||
    actions.invite.isPending ||
    actions.end.isPending;

  if (entry.status === "invited") {
    return (
      <p className="pool-hint">Invitation sent · waiting for them to accept.</p>
    );
  }

  if (entry.status === "ended") {
    return <p className="pool-hint">This relationship has ended. Their history stays on your records.</p>;
  }

  const employed = entry.relationship_type !== "pool" && entry.relationship_type !== "one_off";

  return (
    <div className="rel-controls">
      {!employed && !entry.allows_recontact && (
        <p className="pool-hint">They have turned off contact from venues they have worked for.</p>
      )}

      {entry.relationship_type === "one_off" && entry.allows_recontact && (
        <button
          type="button"
          className="btn primary"
          disabled={busy}
          onClick={() => actions.addToPool.mutate(entry.worker_id)}
        >
          {actions.addToPool.isPending ? "Adding…" : "Add to your team"}
        </button>
      )}

      {entry.relationship_type === "pool" && (
        <button
          type="button"
          className="btn"
          disabled={busy}
          onClick={() => actions.removeFromPool.mutate(entry.worker_id)}
        >
          {actions.removeFromPool.isPending ? "Removing…" : "Remove from your team"}
        </button>
      )}

      {!employed && (
        <div className="rel-invite">
          <select
            className="st-select"
            value={type}
            aria-label="Employment type"
            onChange={(event) => setType(event.target.value as EmployedType)}
          >
            {EMPLOYED.map((item) => (
              <option key={item} value={item}>{RELATIONSHIP_LABELS[item]}</option>
            ))}
          </select>
          <button
            type="button"
            className="btn"
            disabled={busy}
            onClick={() => actions.invite.mutate({ workerId: entry.worker_id, relationship_type: type })}
          >
            {actions.invite.isPending ? "Inviting…" : "Invite to employment"}
          </button>
        </div>
      )}

      <button
        type="button"
        className="btn"
        disabled={busy}
        onClick={() => actions.end.mutate(entry.worker_id)}
      >
        {employed ? "Offboard" : "Remove from records"}
      </button>
    </div>
  );
}
