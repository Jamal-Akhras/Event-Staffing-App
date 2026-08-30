import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "../../lib/api";
import { useShiftsInRange } from "../../lib/useInsights";
import type { Booking, Shift } from "../../types/operations";
import { workerHistory } from "../applications/applicationsUtils";

const HISTORY_DAYS = 180;

export function useWorkerHistory(workerId: string | null, now: Date) {
  const from = new Date(now);
  from.setDate(from.getDate() - HISTORY_DAYS);
  from.setHours(0, 0, 0, 0);
  const to = new Date(now);
  to.setDate(to.getDate() + 1);
  to.setHours(0, 0, 0, 0);

  const shifts = useShiftsInRange(from, to);
  const bookings = useQuery({
    queryKey: ["bookings", workerId],
    enabled: Boolean(workerId),
    queryFn: () => fetchJson<Booking[]>(`/bookings?worker_id=${workerId}&limit=25`),
  });

  if (!workerId) return [];
  return workerHistory(bookings.data ?? ([] as Booking[]), shifts.data ?? ([] as Shift[]), workerId);
}
