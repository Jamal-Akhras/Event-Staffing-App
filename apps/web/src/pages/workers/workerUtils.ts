import type { Application, WorkerProfile } from "../../types/operations";

export type WorkerSort = "name" | "reliability" | "experience";

export type WorkerStats = {
  totalApplications: number;
  approved: number;
  applied: number;
  rejected: number;
};

export function filterAndSortWorkers(
  workers: WorkerProfile[],
  searchQuery: string,
  sortBy: WorkerSort
) {
  const query = searchQuery.trim().toLowerCase();
  const filteredWorkers = query
    ? workers.filter((worker) =>
        [worker.display_name, worker.role, worker.city]
          .join(" ")
          .toLowerCase()
          .includes(query)
      )
    : workers;

  return [...filteredWorkers].sort((left, right) => {
    if (sortBy === "name") {
      return left.display_name.localeCompare(right.display_name);
    }
    if (sortBy === "experience") {
      return right.experience_years - left.experience_years;
    }
    return right.reliability_score - left.reliability_score;
  });
}

export function getWorkerStats(applications: Application[], workerId: string): WorkerStats {
  const workerApplications = applications.filter((item) => item.worker_id === workerId);
  return {
    totalApplications: workerApplications.length,
    approved: countByStatus(workerApplications, "approved"),
    applied: countByStatus(workerApplications, "applied"),
    rejected: countByStatus(workerApplications, "rejected"),
  };
}

function countByStatus(applications: Application[], status: string) {
  return applications.filter((item) => item.status === status).length;
}
