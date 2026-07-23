import type { WorkerSort } from "./workerUtils";

type WorkerFiltersProps = {
  searchQuery: string;
  sortBy: WorkerSort;
  resultCount: number;
  onSearchChange: (value: string) => void;
  onSortChange: (value: WorkerSort) => void;
};

export function WorkerFilters({
  searchQuery,
  sortBy,
  resultCount,
  onSearchChange,
  onSortChange,
}: WorkerFiltersProps) {
  return (
    <div className="card worker-controls">
      <div className="worker-controls-fields">
        <label className="worker-control-label">
          Search
          <input
            className="control-input"
            type="search"
            placeholder="Name, role, or city"
            value={searchQuery}
            onChange={(event) => onSearchChange(event.target.value)}
          />
        </label>

        <label className="worker-control-label">
          Sort
          <select
            className="control-select"
            value={sortBy}
            onChange={(event) => onSortChange(event.target.value as WorkerSort)}
          >
            <option value="reliability">Reliability</option>
            <option value="name">Name</option>
            <option value="experience">Experience</option>
          </select>
        </label>
      </div>
      <span className="pill">{resultCount} shown</span>
    </div>
  );
}
