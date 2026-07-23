import type { WorkerProfile } from "../../types/operations";
import type { WorkerStats } from "./workerUtils";

type WorkerCardProps = {
  worker: WorkerProfile;
  stats: WorkerStats;
  onSelect: () => void;
};

export function WorkerCard({ worker, stats, onSelect }: WorkerCardProps) {
  return (
    <button className="worker-card card" type="button" onClick={onSelect}>
      <div className="worker-card-header">
        <div>
          <h3>{worker.display_name}</h3>
          <p>{worker.role} / {worker.city}</p>
        </div>
        <span className={scoreClassName(worker.reliability_score)}>
          {worker.reliability_score.toFixed(1)}
        </span>
      </div>

      <div className="worker-card-meta">
        <span>{worker.experience_years} years experience</span>
        {worker.languages.length > 0 && <span>{worker.languages.join(", ")}</span>}
      </div>

      {worker.badges.length > 0 && (
        <div className="worker-badges">
          {worker.badges.slice(0, 3).map((badge) => (
            <span key={badge} className="pill">
              {badge}
            </span>
          ))}
          {worker.badges.length > 3 && (
            <span className="pill">+{worker.badges.length - 3} more</span>
          )}
        </div>
      )}

      <div className="worker-card-footer">
        <span>{stats.totalApplications} applications</span>
        <span>{stats.approved} approved</span>
        {stats.applied > 0 && <span>{stats.applied} pending</span>}
      </div>
    </button>
  );
}

function scoreClassName(score: number) {
  if (score >= 0.9) return "worker-score strong";
  if (score >= 0.75) return "worker-score steady";
  return "worker-score watch";
}
