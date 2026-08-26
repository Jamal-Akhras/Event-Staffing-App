export type BillingLine = {
  booking_id: string;
  shift_id: string;
  worker_id: string;
  worker_name: string;
  role: string;
  start_time: string;
  end_time: string;
  completed_at: string;
  hours: string;
  wages: string;
  fee: string;
  total: string;
  waived: boolean;
  state: string;
};

export type Waiver = {
  code: string;
  label: string;
  fee_waived_until: string;
  shift_cap: number;
  shifts_used: number;
  active: boolean;
};

export type BillingSummary = {
  month: string;
  fee_percent: string;
  plan: "founding_partner" | "standard";
  waiver: Waiver | null;
  lines: BillingLine[];
  wages_total: string;
  fee_total: string;
  grand_total: string;
  completed_shifts_all_time: number;
};
