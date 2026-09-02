export type EarningsEntry = {
  booking_id: string;
  shift_id: string;
  role: string;
  location: string;
  start_time: string;
  end_time: string;
  hours: number;
  pay_rate: number;
  total: number;
  status: "paid" | "pending";
  currency: string;
  venue_name?: string | null;
  frozen?: boolean;
};

export type EarningsSummary = {
  period: string;
  total_paid: number;
  total_pending: number;
  currency: string;
  entries: EarningsEntry[];
};

export type Period = "week" | "month" | "year";

export const PERIOD_LABELS: Record<Period, string> = {
  week: "Week",
  month: "Month",
  year: "Year",
};

export { formatMoney, formatDayDate as formatEntryDate } from "../../lib/format";
