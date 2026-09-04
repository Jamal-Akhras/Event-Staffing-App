import { initials } from "../../lib/useVenue";
import { formatMoney } from "../../lib/format";
import { RELATIONSHIP_LABELS } from "../../types/workforce";
import { shortDay } from "../dashboard/dashboardUtils";
import { bucketOf, statusLabel, type DirectoryEntry, type DirectorySort } from "./directory";

const COLUMNS: { key: DirectorySort; label: string; align: "left" | "right" }[] = [
  { key: "name", label: "Person", align: "left" },
  { key: "reliability", label: "Reliability", align: "right" },
  { key: "shifts", label: "Shifts with you", align: "right" },
  { key: "recent", label: "Last worked", align: "right" },
];

type RosterTableProps = {
  rows: DirectoryEntry[];
  sort: DirectorySort;
  currency: string;
  selectedId: string | null;
  onSort: (sort: DirectorySort) => void;
  onSelect: (entry: DirectoryEntry) => void;
};

function relationshipLabel(entry: DirectoryEntry): string {
  if (entry.status === "invited") return "Invited";
  if (entry.status === "ended") return "Past";
  return RELATIONSHIP_LABELS[entry.relationship_type];
}

export function RosterTable({ rows, sort, currency, selectedId, onSort, onSelect }: RosterTableProps) {
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
              <th className="r plain">Cost to date</th>
              <th className="r plain">Relationship</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((entry) => (
              <tr
                key={entry.worker_id}
                className={selectedId === entry.worker_id ? "sel" : ""}
                onClick={() => onSelect(entry)}
              >
                <td>
                  <span className="wk-person">
                    <span className="wk-avatar">{initials(entry.display_name)}</span>
                    <span>
                      <b>{entry.display_name}</b>
                      <span>
                        {[statusLabel(entry), entry.role || "No role set"].filter(Boolean).join(" · ")}
                        {entry.agreed_rate ? ` · ${formatMoney(entry.agreed_rate, currency)}/hr` : ""}
                      </span>
                    </span>
                  </span>
                </td>
                <td className="r">
                  {entry.reliability_score > 0 ? (
                    <span className="wk-rel">
                      <b>{Math.round(entry.reliability_score * 100)}%</b>
                      <span className="wk-track">
                        <i
                          className={entry.reliability_score < 0.8 ? "warn" : ""}
                          style={{ width: `${Math.round(entry.reliability_score * 100)}%` }}
                        />
                      </span>
                    </span>
                  ) : (
                    <span className="wk-quiet">No history</span>
                  )}
                </td>
                <td className="r">{entry.shifts_with_you}</td>
                <td className="r">
                  {entry.last_worked ? shortDay(entry.last_worked) : <span className="wk-quiet">Never</span>}
                </td>
                <td className="r">
                  {entry.shifts_with_you > 0 ? (
                    formatMoney(entry.wages_to_date, currency)
                  ) : (
                    <span className="wk-quiet">—</span>
                  )}
                </td>
                <td className="r">
                  <span className={`wk-tag ${bucketOf(entry)}`}>{relationshipLabel(entry)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
