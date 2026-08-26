export type Shift = {
  shift_id: string;
  operator_id?: string;
  role: string;
  location: string;
  start_time: string;
  end_time: string;
  pay_rate: number;
  status: string;
  created_at: string;
  notes?: string | null;
  workers_needed: number;
  workers_filled: number;
  currency?: string;
  updated_at?: string | null;
  closed_at?: string | null;
  cancelled_at?: string | null;
  cancellation_reason?: string | null;
  cancelled_by_user_id?: string | null;
};

export type Application = {
  application_id: string;
  worker_id: string;
  shift_id: string;
  operator_id: string;
  start_time: string;
  end_time: string;
  status: string;
  message?: string | null;
  booking_id?: string | null;
  created_at: string;
  decided_at?: string | null;
};

export type WorkerProfile = {
  worker_id: string;
  display_name: string;
  role: string;
  city: string;
  experience_years: number;
  reliability_score: number;
  badges: string[];
  bio?: string | null;
  languages: string[];
  updated_at: string;
};

export type Booking = {
  booking_id: string;
  state: string;
  created_at: string;
  no_show_at?: string | null;
  cancellation_reason?: string | null;
  cancelled_by_user_id?: string | null;
};
