import { ShiftCreateForm, type ShiftDraft } from "../../components/ShiftCreateForm";
import "../../components/Modal.css";

export type PostDraft = {
  initial: Partial<ShiftDraft>;
  durationHours?: number;
};

type PostShiftModalProps = {
  draft: PostDraft;
  onClose: () => void;
  onCreated: () => Promise<void>;
  onError: (message: string) => void;
};

export function PostShiftModal({ draft, onClose, onCreated, onError }: PostShiftModalProps) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section className="card modal post-shift-modal" onClick={(event) => event.stopPropagation()}>
        <ShiftCreateForm
          initial={draft.initial}
          durationHours={draft.durationHours}
          onCreated={onCreated}
          onError={onError}
          onCancel={onClose}
        />
      </section>
    </div>
  );
}
