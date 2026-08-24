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

const CURRENCY_SYMBOLS: Record<string, string> = {
  GBP: "£",
  AED: "AED ",
  USD: "$",
};

export function formatMoney(amount: number | string, currency = "GBP"): string {
  const symbol = CURRENCY_SYMBOLS[currency] ?? `${currency} `;
  return `${symbol}${Number(amount).toFixed(2)}`;
}

export function formatEntryDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}
