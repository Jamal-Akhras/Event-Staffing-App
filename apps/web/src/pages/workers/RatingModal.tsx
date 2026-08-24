import { useMemo, useState } from "react";

import { postJson } from "../../lib/api";
import "./RatingModal.css";

export type PendingRating = {
  booking_id: string;
  shift_id: string;
  target_id: string;
  target_name: string;
  target_avatar_url?: string | null;
  shift_role: string;
  shift_location: string;
  start_time: string;
  end_time: string;
};

type Props = {
  rating: PendingRating;
  onDone: () => void;
  onClose: () => void;
};

const STAR_LABELS = ["", "Poor", "Fair", "Good", "Great", "Excellent"];

export function RatingModal({ rating, onDone, onClose }: Props) {
  const [stars, setStars] = useState(0);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const initials = useMemo(
    () => rating.target_name.split(" ").slice(0, 2).map((part) => part[0]).join("").toUpperCase(),
    [rating.target_name],
  );

  async function submit() {
    if (stars === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await postJson(`/bookings/${rating.booking_id}/rate`, {
        stars,
        comment: comment.trim() || undefined,
      });
      onDone();
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <div className="rating-prompt-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="rating-prompt"
        role="dialog"
        aria-modal="true"
        aria-labelledby="rating-prompt-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <span className="rating-prompt-kicker">Shift complete</span>
        {rating.target_avatar_url ? (
          <img className="rating-prompt-avatar" src={rating.target_avatar_url} alt="" />
        ) : (
          <span className="rating-prompt-avatar fallback" aria-hidden="true">{initials}</span>
        )}
        <h2 id="rating-prompt-title">How was {rating.target_name}?</h2>
        <p className="rating-prompt-shift">
          {rating.shift_role} <i /> {formatDate(rating.start_time)}
        </p>

        <div className="rating-prompt-stars" role="radiogroup" aria-label="Choose a rating">
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              key={value}
              type="button"
              className={stars >= value ? "selected" : ""}
              role="radio"
              aria-checked={stars === value}
              aria-label={`${value} star${value === 1 ? "" : "s"}`}
              onClick={() => setStars(value)}
            >
              ★
            </button>
          ))}
        </div>
        <p className="rating-prompt-label">{stars ? STAR_LABELS[stars] : "Select your rating"}</p>

        {stars > 0 && (
          <label className="rating-prompt-feedback">
            <span>Anything else? <em>Optional</em></span>
            <textarea
              value={comment}
              maxLength={1000}
              rows={3}
              placeholder="Share a little more"
              onChange={(event) => setComment(event.target.value)}
            />
          </label>
        )}

        {error && <p className="rating-prompt-error">{error}</p>}

        <button
          className="rating-prompt-submit"
          type="button"
          disabled={stars === 0 || submitting}
          onClick={submit}
        >
          {submitting ? "Sending…" : "Submit rating"}
        </button>
        <button className="rating-prompt-later" type="button" onClick={onClose}>Not now</button>
      </section>
    </div>
  );
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}
