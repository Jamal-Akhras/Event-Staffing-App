import { useState } from "react";
import "./CancellationModal.css";

type CancellationModalProps = {
  title: string;
  consequence: string;
  confirmLabel: string;
  onClose: () => void;
  onConfirm: (reason: string) => Promise<void>;
};

export function CancellationModal({
  title,
  consequence,
  confirmLabel,
  onClose,
  onConfirm,
}: CancellationModalProps) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirm() {
    if (reason.trim().length < 3) {
      setError("Add a short reason before continuing.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await onConfirm(reason.trim());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section className="card cancellation-modal" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <div>
            <p className="cancellation-eyebrow">Confirmation required</p>
            <h2>{title}</h2>
          </div>
          <button className="btn ghost" type="button" onClick={onClose}>Back</button>
        </div>
        <div className="cancellation-modal-body">
          <p>{consequence}</p>
          <label>
            Reason
            <textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Give the other person useful context"
              rows={4}
              autoFocus
            />
          </label>
          {error && <p className="status error">{error}</p>}
          <button className="btn danger" disabled={busy} type="button" onClick={confirm}>
            {busy ? "Working..." : confirmLabel}
          </button>
        </div>
      </section>
    </div>
  );
}
