import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "../lib/api";
import { initials } from "../lib/useVenue";
import type { WorkerProfile } from "../types/operations";
import "./WorkerRail.css";

type WorkerRatingSummary = { avg_stars: number | null; total_ratings: number };

export type RailStat = { label: string; value: string };
export type RailEvent = { label: string; when: string };

type WorkerRailProps = {
  worker: WorkerProfile;
  kicker: string;
  stats: RailStat[];
  history: RailEvent[];
  historyTitle: string;
  actions?: ReactNode;
  note?: { kicker: string; title: string; body: string };
};

export function stars(average: number) {
  const filled = Math.round(average);
  return "★★★★★".slice(0, filled) + "☆☆☆☆☆".slice(0, 5 - filled);
}

export function WorkerRail({ worker, kicker, stats, history, historyTitle, actions, note }: WorkerRailProps) {
  const rating = useQuery({
    queryKey: ["worker-rating", worker.worker_id],
    queryFn: () => fetchJson<WorkerRatingSummary>(`/workers/${worker.worker_id}/rating-summary`),
  });
  const summary = rating.data;
  const ratingValue = summary && summary.avg_stars !== null ? stars(summary.avg_stars) : "Not rated";

  return (
    <div className="rail">
      <div className="rail-card">
        <span className="rail-kicker">{kicker}</span>
        <div className="rail-person">
          <span className="rail-avatar">{initials(worker.display_name || "Worker")}</span>
          <div>
            <b>{worker.display_name}</b>
            <span>
              {worker.role} · {worker.city}
              {worker.experience_years > 0 ? ` · ${worker.experience_years} years` : ""}
            </span>
          </div>
        </div>

        <div className="rail-stats">
          <div>
            <span>Reliability</span>
            <b>{worker.reliability_score > 0 ? `${Math.round(worker.reliability_score * 100)}%` : "No history"}</b>
          </div>
          <div>
            <span>Your rating</span>
            <b className={summary && summary.avg_stars !== null ? "rail-stars" : "rail-quiet"}>{ratingValue}</b>
          </div>
          {stats.map((stat) => (
            <div key={stat.label}>
              <span>{stat.label}</span>
              <b>{stat.value}</b>
            </div>
          ))}
        </div>

        {worker.bio && (
          <section className="rail-section">
            <h4>About</h4>
            <p>{worker.bio}</p>
          </section>
        )}

        {worker.languages.length > 0 && (
          <section className="rail-section">
            <h4>Languages</h4>
            <div className="rail-tags">
              {worker.languages.map((language) => (
                <span key={language}>{language}</span>
              ))}
            </div>
          </section>
        )}

        {worker.badges.length > 0 && (
          <section className="rail-section">
            <h4>Badges</h4>
            <div className="rail-tags">
              {worker.badges.map((badge) => (
                <span key={badge}>{badge}</span>
              ))}
            </div>
          </section>
        )}

        <section className="rail-section">
          <h4>{historyTitle}</h4>
          {history.length === 0 ? (
            <p>No shifts with you yet.</p>
          ) : (
            <div className="rail-history">
              {history.map((item) => (
                <div key={`${item.label}-${item.when}`}>
                  <span>{item.label}</span>
                  <em>{item.when}</em>
                </div>
              ))}
            </div>
          )}
        </section>

        {actions && <div className="rail-actions">{actions}</div>}
      </div>

      {note && (
        <div className="rail-note">
          <span className="rail-kicker">{note.kicker}</span>
          <b>{note.title}</b>
          <p>{note.body}</p>
        </div>
      )}
    </div>
  );
}
