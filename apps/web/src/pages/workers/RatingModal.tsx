import { useState } from "react";

import { postJson } from "../../lib/api";

type Props = {
  bookingId: string;
  workerName: string;
  shiftRole: string;
  shiftLocation: string;
  shiftDate: string;
  onDone: () => void;
  onClose: () => void;
};

export function RatingModal({ bookingId, workerName, shiftRole, shiftLocation, shiftDate, onDone, onClose }: Props) {
  const [stars, setStars] = useState(0);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (stars === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await postJson(`/bookings/${bookingId}/rate`, { stars, comment: comment || undefined });
      onDone();
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  };

  return (
    <div className="worker-modal-backdrop" onClick={onClose}>
      <section className="card worker-modal" style={{ maxWidth: 480, gap: 18 }} onClick={(e) => e.stopPropagation()}>
        <div>
          <p className="booking-id">Rate worker</p>
          <h2 style={{ margin: "4px 0" }}>{workerName}</h2>
          <p className="booking-meta">{shiftRole} · {shiftLocation} · {shiftDate}</p>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => setStars(n)}
              style={{
                fontSize: "2rem",
                background: "none",
                border: "none",
                cursor: "pointer",
                color: stars >= n ? "#F59E0B" : "var(--border-soft)",
                padding: "2px 4px",
              }}
            >
              ★
            </button>
          ))}
        </div>

        <label className="settings-label">
          <span>Comment (optional)</span>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="How did this worker perform?"
            rows={3}
            style={{ resize: "vertical" }}
          />
        </label>

        {error && <p style={{ margin: 0, color: "var(--error)", fontWeight: 700 }}>{error}</p>}

        <div className="actions">
          <button
            className="btn primary"
            type="button"
            disabled={stars === 0 || submitting}
            onClick={submit}
          >
            {submitting ? "Submitting…" : "Submit rating"}
          </button>
          <button className="btn ghost" type="button" onClick={onClose}>
            Cancel
          </button>
        </div>
      </section>
    </div>
  );
}
