import { useEffect } from "react";
import type { WorkerProfile } from "../types/operations";
import "./WorkerProfilePanel.css";

type WorkerProfilePanelProps = {
  profile: WorkerProfile;
  onClose: () => void;
};

export function WorkerProfilePanel({ profile, onClose }: WorkerProfilePanelProps) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="worker-profile-backdrop" onClick={onClose}>
      <section
        className="card worker-profile-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="worker-profile-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="worker-profile-header">
          <div>
            <p className="booking-id">{profile.worker_id}</p>
            <h2 id="worker-profile-title">{profile.display_name}</h2>
            <p>{profile.role} - {profile.city}</p>
          </div>
          <button className="btn ghost" type="button" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="worker-profile-body">
          <div className="worker-profile-stats">
            <div className="worker-profile-stat">
              <span>Experience</span>
              <strong>{profile.experience_years} years</strong>
            </div>

            <div className="worker-profile-stat">
              <span>Reliability Score</span>
              <strong>{profile.reliability_score.toFixed(2)}</strong>
            </div>
          </div>

          {profile.bio && (
            <div className="worker-profile-section">
              <h3>Bio</h3>
              <p>{profile.bio}</p>
            </div>
          )}

          {profile.languages.length > 0 && (
            <TokenGroup title="Languages" items={profile.languages} />
          )}

          {profile.badges.length > 0 && (
            <TokenGroup title="Badges" items={profile.badges} accent />
          )}
        </div>
      </section>
    </div>
  );
}

function TokenGroup({
  title,
  items,
  accent = false,
}: {
  title: string;
  items: string[];
  accent?: boolean;
}) {
  return (
    <div className="worker-profile-section">
      <h3>{title}</h3>
      <div className="worker-profile-token-list">
        {items.map((item) => (
          <span
            key={item}
            className={`pill ${accent ? "worker-profile-token-accent" : ""}`}
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
