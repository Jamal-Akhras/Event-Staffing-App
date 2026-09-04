export type BillingLine = {
  line_id: string;
  line_kind: "charge" | "correction";
  charge_id: string;
  adjustment_id: string | null;
  reason: string | null;
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

export type SubscriptionLine = {
  subscription_charge_id: string;
  period: string;
  plan: string;
  amount: string;
};

export type BoostLine = {
  boost_id: string;
  shift_id: string;
  tier: string;
  price: string;
};

export type BillingSummary = {
  month: string;
  fee_percent: string;
  plan: string;
  waiver: Waiver | null;
  lines: BillingLine[];
  subscription_lines: SubscriptionLine[];
  boost_lines: BoostLine[];
  wages_total: string;
  fee_total: string;
  subscription_total: string;
  boost_total: string;
  amount_due: string;
  completed_shifts_all_time: number;
};
