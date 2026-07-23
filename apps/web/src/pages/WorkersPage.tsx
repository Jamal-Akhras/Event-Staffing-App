import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { fetchJson } from "../lib/api";
import type { Application, WorkerProfile } from "../types/operations";
import { WorkerCard } from "./workers/WorkerCard";
import { WorkerDetailModal } from "./workers/WorkerDetailModal";
import { WorkerFilters } from "./workers/WorkerFilters";
import {
  filterAndSortWorkers,
  getWorkerStats,
  type WorkerSort,
} from "./workers/workerUtils";
import "./WorkersPage.css";

export function WorkersPage() {
  const [workers, setWorkers] = useState<WorkerProfile[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<WorkerSort>("reliability");
  const [selectedWorker, setSelectedWorker] = useState<WorkerProfile | null>(null);

  const loadWorkers = async () => {
    setLoading(true);
    try {
      const [workerData, applicationData] = await Promise.all([
        fetchJson<WorkerProfile[]>("/workers"),
        fetchJson<Application[]>("/applications").catch(() => [] as Application[]),
      ]);
      setWorkers(workerData);
      setApplications(applicationData);
      setError(null);
    } catch (err) {
      setWorkers([]);
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadWorkers(); }, []);

  const sortedWorkers = useMemo(
    () => filterAndSortWorkers(workers, searchQuery, sortBy),
    [workers, searchQuery, sortBy]
  );

  const selectedStats = selectedWorker
    ? getWorkerStats(applications, selectedWorker.worker_id)
    : null;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Workers</h1>
          <p className="page-subtitle">
            {loading ? "Loading…" : `${workers.length} worker${workers.length !== 1 ? "s" : ""} who have worked here`}
          </p>
        </div>
        <button className="btn secondary" type="button" onClick={loadWorkers}>
          Refresh
        </button>
      </div>

      {error && (
        <div className="card error-card">
          <p className="status error">{error}</p>
        </div>
      )}

      <WorkerFilters
        searchQuery={searchQuery}
        sortBy={sortBy}
        resultCount={sortedWorkers.length}
        onSearchChange={setSearchQuery}
        onSortChange={setSortBy}
      />

      {loading ? (
        <div className="card">
          <p className="booking-meta">Loading workers...</p>
        </div>
      ) : sortedWorkers.length === 0 ? (
        <EmptyState
          title={searchQuery ? "No workers found" : "No workers yet"}
          message={
            searchQuery
              ? `No workers match "${searchQuery}". Try a different search term.`
              : "Workers who have completed a shift here and opted in to being visible will appear in this list."
          }
          action={searchQuery ? { label: "Clear Search", onClick: () => setSearchQuery("") } : undefined}
        />
      ) : (
        <div className="workers-grid">
          {sortedWorkers.map((worker) => (
            <WorkerCard
              key={worker.worker_id}
              worker={worker}
              stats={getWorkerStats(applications, worker.worker_id)}
              onSelect={() => setSelectedWorker(worker)}
            />
          ))}
        </div>
      )}

      {selectedWorker && selectedStats && (
        <WorkerDetailModal
          worker={selectedWorker}
          stats={selectedStats}
          onClose={() => setSelectedWorker(null)}
        />
      )}
    </div>
  );
}
