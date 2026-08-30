import { stars } from "../../components/WorkerRail";
import { initials } from "../../lib/useVenue";
import { shortDay } from "../dashboard/dashboardUtils";
import { STANDING_LABELS, type RosterRow, type RosterSort } from "./rosterUtils";

const COLUMNS: { key: RosterSort; label: string; align: "left" | "right" }[] = [
  { key: "name", label: "Worker", align: "left" },
  { key: "reliability", label: "Reliability", align: "right" },
  { key: "shifts", label: "Shifts with you", align: "right" },
  { key: "recent", label: "Last worked", align: "right" },
];

type RosterTableProps = {
  rows: RosterRow[];
  sort: RosterSort;
  selectedId: string | null;
  onSort: (sort: RosterSort) => void;
  onSelect: (row: RosterRow) => void;
};

export function RosterTable({ rows, sort, selectedId, onSort, onSelect }: RosterTableProps) {
  return (
    <div className="wk-table-wrap">
      <div className="wk-scroll">
        <table className="wk-table">
          <thead>
            <tr>
              {COLUMNS.map((column) => (
                <th key={column.key} className={column.align === "right" ? "r" : ""}>
                  <button
                    type="button"
                    className={sort === column.key ? "on" : ""}
                    onClick={() => onSort(column.key)}
                  >
                    {column.label}
                    {sort === column.key && <span aria-hidden="true"> ↓</span>}
                  </button>
                </th>
              ))}
              <th className="r plain">Your rating</th>
              <th className="r plain">Standing</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.worker.worker_id}
                className={selectedId === row.worker.worker_id ? "sel" : ""}
                onClick={() => onSelect(row)}
              >
                <td>
                  <span className="wk-person">
                    <span className="wk-avatar">{initials(row.worker.display_name || "Worker")}</span>
                    <span>
                      <b>{row.worker.display_name}</b>
                      <span>
                        {row.worker.role} · {row.worker.city}
                      </span>
                    </span>
                  </span>
                </td>
                <td className="r">
                  {row.worker.reliability_score > 0 ? (
                    <span className="wk-rel">
                      <b>{Math.round(row.worker.reliability_score * 100)}%</b>
                      <span className="wk-track">
                        <i
                          className={row.worker.reliability_score < 0.8 ? "warn" : ""}
                          style={{ width: `${Math.round(row.worker.reliability_score * 100)}%` }}
                        />
                      </span>
                    </span>
                  ) : (
                    <span className="wk-quiet">No history</span>
                  )}
                </td>
                <td className="r">{row.shiftsWithYou}</td>
                <td className="r">{row.lastWorked ? shortDay(row.lastWorked) : <span className="wk-quiet">Never</span>}</td>
                <td className="r">
                  {row.rating === null ? <span className="wk-quiet">—</span> : <span className="wk-stars">{stars(row.rating)}</span>}
                </td>
                <td className="r">
                  <span className={`wk-tag ${row.standing}`}>{STANDING_LABELS[row.standing]}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
