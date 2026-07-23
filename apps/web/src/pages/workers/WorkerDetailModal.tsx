import { useEffect, useState } from "react";

import { fetchJson } from "../../lib/api";
import type { WorkerProfile } from "../../types/operations";
import type { WorkerStats } from "./workerUtils";

type RatingSummary = { avg_stars: number | null; total_ratings: number };

type WorkerDetailModalProps = {
  worker: WorkerProfile;
  stats: WorkerStats;
  onClose: () => void;
};

export function WorkerDetailModal({ worker, stats, onClose }: WorkerDetailModalProps) {
  const [rating, setRating] = useState<RatingSummary | null>(null);

  useEffect(() => {
    fetchJson<RatingSummary>(`/workers/${worker.worker_id}/rating-summary`)
      .then(setRating)
      .catch(() => {});
  }, [worker.worker_id]);

  const starsDisplay = rating?.avg_stars != null
    ? `${rating.avg_stars.toFixed(1)} ★ (${rating.total_ratings})`
    : rating ? "No ratings yet" : "—";

  return (
    <div className="worker-modal-backdrop" onClick={onClose}>
      <section className="card worker-modal" onClick={(event) => event.stopPropagation()}>
        <div className="worker-modal-header">
          <div>
            <p className="booking-id">{worker.worker_id}</p>
            <h2>{worker.display_name}</h2>
            <p>{worker.role} / {worker.city}</p>
          </div>
          <button className="btn secondary" type="button" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="worker-modal-metrics">
          <Metric label="Reliability" value={worker.reliability_score.toFixed(2)} />
          <Metric label="Experience" value={`${worker.experience_years} yr`} />
          <Metric label="Rating" value={starsDisplay} />
          <Metric label="Applications" value={String(stats.totalApplications)} />
        </div>

        {worker.bio && (
          <section className="worker-modal-section">
            <h3>Bio</h3>
            <p>{worker.bio}</p>
          </section>
        )}

        {worker.languages.length > 0 && (
          <TagSection title="Languages" values={worker.languages} />
        )}

        {worker.badges.length > 0 && (
          <TagSection title="Badges" values={worker.badges} />
        )}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="application-card worker-modal-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function TagSection({ title, values }: { title: string; values: string[] }) {
  return (
    <section className="worker-modal-section">
      <h3>{title}</h3>
      <div className="worker-badges">
        {values.map((value) => (
          <span key={value} className="pill">
            {value}
          </span>
        ))}
      </div>
    </section>
  );
}
