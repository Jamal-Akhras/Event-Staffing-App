import { Link } from "react-router-dom";

import type { AttentionItem } from "./dashboardUtils";

type AttentionQueueProps = {
  items: AttentionItem[];
};

export function AttentionQueue({ items }: AttentionQueueProps) {
  return (
    <section className="card attention-panel">
      <div className="dashboard-section-header">
        <div>
          <h2>Attention Queue</h2>
          <p>What needs action before the next service window.</p>
        </div>
      </div>

      <div className="attention-list">
        {items.map((item) => (
          <div key={item.label} className={`attention-item ${item.tone}`}>
            <div>
              <span className="attention-value">{item.value}</span>
            </div>
            <div>
              <h3>{item.label}</h3>
              <p>{item.note}</p>
            </div>
            <Link className="btn ghost" to={item.to}>
              {item.action}
            </Link>
          </div>
        ))}
      </div>
    </section>
  );
}
