import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "../lib/api";
import { MessageThread } from "./MessageThread";
import "./Modal.css";

type EmploymentThread = {
  relationship_id: string;
  worker_id: string;
  role: string | null;
  venue_name: string;
};

export function EmploymentThreads() {
  const [selected, setSelected] = useState<EmploymentThread | null>(null);
  const threads = useQuery({
    queryKey: ["employment-threads"],
    queryFn: () => fetchJson<EmploymentThread[]>("/venues/me/employment-threads"),
  });

  return (
    <section className="card" style={{ padding: 18, marginBottom: 18 }}>
      <h3 style={{ marginTop: 0 }}>Staff messages</h3>
      <p className="booking-meta">Standing conversations with permanent, part-time and bank staff.</p>
      {threads.isLoading && <p className="booking-meta">Loading…</p>}
      {threads.error && <p className="status error">{(threads.error as Error).message}</p>}
      <div className="st-inline">
        {(threads.data ?? []).map((thread) => (
          <button className="st-btn" key={thread.relationship_id} type="button" onClick={() => setSelected(thread)}>
            {thread.role ?? thread.worker_id}
          </button>
        ))}
      </div>
      {threads.data?.length === 0 && <p className="booking-meta">No employed staff channels yet.</p>}

      {selected && (
        <div className="modal-backdrop" onClick={() => setSelected(null)}>
          <section className="card modal" onClick={(event) => event.stopPropagation()}>
            <header className="modal-header">
              <div><h2>{selected.role ?? "Staff member"}</h2><p>{selected.venue_name}</p></div>
              <button className="btn ghost" type="button" onClick={() => setSelected(null)}>Close</button>
            </header>
            <MessageThread kind="employment" relationshipId={selected.relationship_id} />
          </section>
        </div>
      )}
    </section>
  );
}
